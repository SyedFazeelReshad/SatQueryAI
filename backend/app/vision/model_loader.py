"""
SatQuery AI — VLM Model Loader (Singleton)
Stage 2: Loads Qwen2-VL-2B-Instruct + LoRA adapter exactly once
and serves all inference requests from the cached model instance.

Design Principles:
- Load once at server startup (avoids 20-30s reload per request)
- Graceful fallback: if adapter not found → Stage 1 stubs
- Device-agnostic: auto-selects CUDA > MPS > CPU
- Configurable via configs/models.yaml
"""

import logging
import time
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Sentinel values for deferred imports
_transformers = None
_peft = None
_qwen_vl_utils = None
_torch = None


def _try_import_stage2_deps() -> bool:
    """Attempt to import Stage 2 ML dependencies. Returns True if all available."""
    global _transformers, _peft, _qwen_vl_utils, _torch
    try:
        import torch as _t
        import transformers as _tr
        import peft as _p
        _torch = _t
        _transformers = _tr
        _peft = _p
        try:
            import qwen_vl_utils as _qvl
            _qwen_vl_utils = _qvl
        except ImportError:
            _qwen_vl_utils = None  # Not strictly required at runtime
        return True
    except ImportError as e:
        logger.warning(f"Stage 2 ML dependencies not installed: {e}")
        logger.warning("Running in Stage 1 stub mode. Install requirements_stage2.txt to enable VLM.")
        return False


def _select_device() -> str:
    """Auto-select best available compute device."""
    if _torch is None:
        return "cpu"
    if _torch.cuda.is_available():
        return "cuda"
    if hasattr(_torch.backends, "mps") and _torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class QwenVLModelSingleton:
    """
    Thread-safe singleton loader for Qwen2-VL-2B + LoRA adapter.
    Call `get_instance()` from anywhere in the backend — model is loaded once.
    """
    _instance: Optional["QwenVLModelSingleton"] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.model = None
        self.processor = None
        self.device = "cpu"
        self.stage = 1
        self.model_name = "Qwen/Qwen2-VL-2B-Instruct"
        self.adapter_path: Optional[Path] = None
        self._initialized = True

    def load(self, model_name: str, adapter_path: str, device: str = "auto") -> bool:
        """
        Load Qwen2-VL base model + LoRA adapter from disk.
        Returns True if loaded successfully, False if falling back to stub.
        """
        if not _try_import_stage2_deps():
            logger.warning("Staying in Stage 1 (stub) mode — Stage 2 deps not installed.")
            return False

        # Search candidate directories (direct, relative to backend, or subfolders)
        candidates = [
            Path(adapter_path),
            Path("..") / adapter_path,
            Path(__file__).resolve().parent.parent.parent.parent / adapter_path
        ]
        
        # Also check immediate subdirectories in candidates (e.g. unzipped folder)
        expanded_candidates = []
        for c in candidates:
            if c.exists() and c.is_dir():
                expanded_candidates.append(c)
                for sub in c.iterdir():
                    if sub.is_dir():
                        expanded_candidates.append(sub)
                        
        resolved_adapter = None
        for candidate in expanded_candidates:
            if (candidate / "adapter_config.json").exists() and (candidate / "adapter_model.safetensors").exists():
                resolved_adapter = candidate
                break

        if resolved_adapter is None:
            logger.warning(
                f"LoRA adapter not found in '{adapter_path}' or its subdirectories. "
                "Staying in Stage 1 stub mode."
            )
            return False

        adapter_dir = resolved_adapter
        logger.info(f"Resolved valid LoRA adapter directory at: {adapter_dir}")

        resolved_device = _select_device() if device == "auto" else device
        self.device = resolved_device
        self.model_name = model_name
        self.adapter_path = adapter_dir

        logger.info(f"Loading Qwen2-VL base model: {model_name} on {resolved_device}...")
        t0 = time.time()

        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
            from peft import PeftModel

            # Load processor
            self.processor = AutoProcessor.from_pretrained(
                model_name,
                min_pixels=256 * 28 * 28,
                max_pixels=1280 * 28 * 28,
                trust_remote_code=True
            )

            # Load base model
            base_model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                torch_dtype="auto",
                device_map=resolved_device,
                trust_remote_code=True
            )

            # Apply LoRA adapter
            logger.info(f"Applying LoRA adapter from {adapter_dir}...")
            self.model = PeftModel.from_pretrained(base_model, str(adapter_dir))
            self.model.eval()

            elapsed = time.time() - t0
            self.stage = 2
            logger.info(f"Qwen2-VL + LoRA adapter loaded in {elapsed:.1f}s on {resolved_device}.")
            return True

        except Exception as e:
            logger.error(f"Failed to load Qwen2-VL + adapter: {e}")
            self.model = None
            self.processor = None
            return False

    def is_available(self) -> bool:
        return self.model is not None and self.processor is not None

    def infer(
        self,
        images: list,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1
    ) -> str:
        """
        Run Qwen2-VL inference.
        
        Args:
            images: List of PIL.Image or np.ndarray objects
            prompt: Text prompt string
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Generated text answer string.
        """
        if not self.is_available():
            return "[Stage 1: VLM not yet available. Deterministic analysis results shown above.]"

        try:
            # CPU Performance Acceleration
            if self.device == "cpu":
                import os
                _torch.set_num_threads(min(os.cpu_count() or 4, 6))
                max_new_tokens = min(max_new_tokens, 140)

            # Convert numpy arrays to PIL and resize for CPU efficiency
            pil_images = []
            for img in images:
                if isinstance(img, np.ndarray):
                    if img.dtype != np.uint8:
                        img = (img * 255).clip(0, 255).astype(np.uint8)
                    if img.shape[-1] > 3:
                        img = img[:, :, :3]  # Take first 3 bands as RGB
                    p_img = Image.fromarray(img)
                elif isinstance(img, Image.Image):
                    p_img = img.copy()
                else:
                    p_img = img

                # Scale down resolution on CPU to dramatically reduce visual tokens
                if self.device == "cpu" and isinstance(p_img, Image.Image):
                    p_img.thumbnail((384, 384), Image.Resampling.LANCZOS)
                pil_images.append(p_img)

            # Build Qwen2-VL conversation
            messages = [{"role": "user", "content": []}]
            for pil_img in pil_images:
                messages[0]["content"].append({"type": "image", "image": pil_img})
            messages[0]["content"].append({"type": "text", "text": prompt})

            # Tokenize
            text_input = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.processor(
                text=[text_input],
                images=pil_images if pil_images else None,
                return_tensors="pt",
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate with optimized settings
            with _torch.inference_mode():
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=(temperature > 0.01),
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )

            # Decode (only the generated portion, not input prompt)
            input_len = inputs["input_ids"].shape[1]
            generated = output_ids[:, input_len:]
            answer = self.processor.batch_decode(
                generated, skip_special_tokens=True, clean_up_tokenization_spaces=True
            )[0].strip()

            return answer

        except Exception as e:
            logger.error(f"Qwen2-VL inference error: {e}")
            return f"[VLM inference error: {str(e)[:120]}. Deterministic results are available above.]"


# Module-level singleton access
_singleton = QwenVLModelSingleton()


def get_vlm() -> QwenVLModelSingleton:
    """Returns the shared Qwen2-VL singleton instance."""
    return _singleton


def initialize_vlm_from_config(config_path: str = "configs/models.yaml") -> bool:
    """
    Initialize the VLM singleton from the project YAML config.
    Called once at FastAPI startup. Returns True if Stage 2 activated.
    """
    try:
        import yaml
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)

        vlm_cfg = cfg.get("primary_vlm", {})
        stage = vlm_cfg.get("stage", 1)
        model_name = vlm_cfg.get("model_name", "Qwen/Qwen2-VL-2B-Instruct")
        adapter_path = vlm_cfg.get("adapter_path", "models/trained/rs_vlm_lora/")
        device = vlm_cfg.get("device", "auto")

        if stage >= 2:
            logger.info(f"Stage {stage} detected — attempting to load Qwen2-VL...")
            return _singleton.load(model_name, adapter_path, device)
        else:
            logger.info("Stage 1 mode — VLM stubs active.")
            return False

    except Exception as e:
        logger.warning(f"Could not load VLM config: {e}. Defaulting to Stage 1 stubs.")
        return False
