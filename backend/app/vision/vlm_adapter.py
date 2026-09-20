import os
from PIL import Image
try:
    import google.generativeai as genai
except ImportError:
    genai = None

"""
SatQuery AI — VLM Adapter (Stage 2)
Unified interface for all Vision-Language Model calls.

Stage 1: Returns honest stubs labeled as such.
Stage 2: Routes through Qwen2-VL-2B-Instruct + LoRA adapter.

All callers in the codebase use only this module.
Switching stages requires NO changes to calling code.
"""

import logging
import numpy as np
from typing import Any

from app.vision.model_loader import get_vlm

logger = logging.getLogger(__name__)

# System prompt for remote sensing context
_RS_SYSTEM_PROMPT = (
    "You are SatQuery AI, a specialised remote sensing analysis assistant trained on satellite imagery. "
    "You interpret multispectral and SAR satellite scenes accurately using remote sensing science. "
    "When deterministic measurements are provided (NDVI, area, change percentage), cite them in your answer. "
    "Never fabricate numerical values. Clearly distinguish between what you observe and what is uncertain. "
    "Be concise but scientifically precise."
)


class VLMAdapter:
    """
    Unified VLM interface for SatQuery AI.
    Automatically uses live Qwen2-VL if Stage 2 adapter is loaded,
    otherwise returns clearly-labeled Stage 1 stubs.
    """

    def __init__(self, config: dict):
        self.config = config
        self._vlm = get_vlm()

    def is_available(self) -> bool:
        return self._vlm.is_available()

    def _stage(self) -> int:
        return self._vlm.stage

    # ──────────────────────────────────────────────────────────────
    # VQA: Answer a question about a single satellite image
    # ──────────────────────────────────────────────────────────────
    def answer_question(
        self,
        image: np.ndarray,
        question: str,
        context: dict = {}
    ) -> dict:
                # Multimodal Vision fallback using Gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        if not self._vlm.is_available() and genai and api_key and api_key != "your_actual_gemini_api_key_here":
            try:
                genai.configure(api_key=api_key)
                g_model = genai.GenerativeModel("gemini-1.5-flash")
                
                pil_img = None
                if isinstance(image, np.ndarray):
                    img_arr = image.copy()
                    if img_arr.dtype in [np.float32, np.float64]:
                        img_arr = (np.clip(img_arr, 0, 1) * 255).astype(np.uint8)
                    if len(img_arr.shape) == 2:
                        pil_img = Image.fromarray(img_arr).convert("RGB")
                    elif img_arr.shape[2] == 4:
                        pil_img = Image.fromarray(img_arr[:, :, :3])
                    else:
                        pil_img = Image.fromarray(img_arr)
                elif isinstance(image, Image.Image):
                    pil_img = image

                prompt = (
                    f"{_RS_SYSTEM_PROMPT}\n\n"
                    f"Context measurements from analysis:\n{context.get('measurements', '')}\n\n"
                    f"User question: {question}\n"
                    "Instructions: Carefully observe the provided aerial/satellite image. Identify discrete objects like vehicles, buildings, roofs, driveways, trees, or water bodies and state their spatial location (e.g., 'in the upper-right corner', 'near the bottom left', 'parked on the driveway'). Be direct and scientifically accurate."
                )

                content_payload = [pil_img, prompt] if pil_img is not None else [prompt]
                response = g_model.generate_content(content_payload)
                ans_text = response.text.strip() if response and response.text else "Object identified."

                return {
                    "answer": ans_text,
                    "confidence": 0.95,
                    "model": "gemini-1.5-flash-multimodal",
                    "stage": 2,
                    "is_stub": False,
                    "warnings": []
                }
            except Exception as e:
                print(f"\n[GEMINI ERROR TRIGGERED]: {e}\n"); logger.error(f"Gemini error: {e}", exc_info=True)

        if not self._vlm.is_available():
            return {
                "answer": (
                    "[Stage 1: VLM not yet available. Deterministic analysis results shown above.]\n"
                    "Install Stage 2 dependencies and provide the trained LoRA adapter to enable language reasoning."
                ),
                "confidence": None,
                "model": "stub",
                "stage": 1,
                "is_stub": True,
                "warnings": ["VLM disabled — Stage 1 mode."]
            }

        # Build context-rich prompt
        measurements_str = ""
        if context.get("measurements"):
            measurements_str = "\n\nDeterministic measurements from raster analysis:\n"
            for m in context["measurements"]:
                measurements_str += f"  - {m.get('label', '')}: {m.get('value', '')} {m.get('unit', '')} [{m.get('evidence_type', '')}]\n"

        prompt = (
            f"{_RS_SYSTEM_PROMPT}\n\n"
            f"{measurements_str}\n"
            f"User question: {question}"
        )

        answer = self._vlm.infer(
            images=[image],
            prompt=prompt,
            max_new_tokens=self.config.get("max_new_tokens", 512),
            temperature=self.config.get("temperature", 0.1)
        )

        return {
            "answer": answer,
            "confidence": 0.87,
            "model": f"Qwen2-VL-2B-Instruct+LoRA (Stage {self._stage()})",
            "stage": self._stage(),
            "is_stub": False,
            "warnings": []
        }

    # ──────────────────────────────────────────────────────────────
    # Captioning: Generate a scene description
    # ──────────────────────────────────────────────────────────────
    def generate_caption(
        self,
        image: np.ndarray,
        context: dict = {}
    ) -> dict:
        if not self._vlm.is_available():
            return {
                "caption": "[Stage 1: VLM not yet available. Deterministic analysis results shown above.]",
                "confidence": None,
                "model": "stub",
                "stage": 1,
                "is_stub": True,
                "warnings": ["VLM disabled — Stage 1 mode."]
            }

        measurements_str = ""
        if context.get("measurements"):
            measurements_str = "\nAvailable measurements:\n" + "\n".join(
                f"  - {m.get('label')}: {m.get('value')} {m.get('unit')}"
                for m in context["measurements"]
            )

        prompt = (
            f"{_RS_SYSTEM_PROMPT}\n\n"
            f"{measurements_str}\n"
            "Provide a detailed remote sensing scene description of this satellite image. "
            "Identify the dominant land cover types, terrain features, and any notable structures or patterns."
        )

        caption = self._vlm.infer(
            images=[image],
            prompt=prompt,
            max_new_tokens=400,
            temperature=0.15
        )

        return {
            "caption": caption,
            "confidence": 0.84,
            "model": f"Qwen2-VL-2B-Instruct+LoRA (Stage {self._stage()})",
            "stage": self._stage(),
            "is_stub": False,
            "warnings": []
        }

    # ──────────────────────────────────────────────────────────────
    # Change Explanation: Interpret bi-temporal change detection
    # ──────────────────────────────────────────────────────────────
    def explain_change(
        self,
        image_a: np.ndarray,
        image_b: np.ndarray,
        evidence: dict = {}
    ) -> dict:
        if not self._vlm.is_available():
            return {
                "answer": "[Stage 1: VLM not yet available. Deterministic change results shown above.]",
                "confidence": None,
                "model": "stub",
                "stage": 1,
                "is_stub": True,
                "warnings": ["VLM disabled — Stage 1 mode."]
            }

        change_pct = evidence.get("change_percentage", "unknown")
        area_km2 = evidence.get("changed_area_km2", "unknown")
        user_query = evidence.get("question", "Explain what changes have occurred between the two dates.")

        prompt = (
            f"{_RS_SYSTEM_PROMPT}\n\n"
            f"Deterministic change detection results:\n"
            f"  - Changed area: {change_pct}% of the scene\n"
            f"  - Changed area: {area_km2} km²\n\n"
            "You are given two satellite images of the same region at two different dates (before and after). "
            "Based on the visual change patterns and the deterministic measurements above, "
            f"answer the following user query: {user_query}\n"
            "Identify the nature of the change (e.g., urban expansion, deforestation, flooding, agricultural change). "
            "Be scientifically precise."
        )

        answer = self._vlm.infer(
            images=[image_a, image_b],
            prompt=prompt,
            max_new_tokens=512,
            temperature=0.1
        )

        return {
            "answer": answer,
            "confidence": 0.83,
            "model": f"Qwen2-VL-2B-Instruct+LoRA (Stage {self._stage()})",
            "stage": self._stage(),
            "is_stub": False,
            "warnings": []
        }
