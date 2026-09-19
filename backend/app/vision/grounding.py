"""
SatQuery AI — Grounding Module (Stage 2)
Text-guided object detection using Grounding DINO 1.5 Edge
+ Promptable pixel segmentation using MobileSAM v2.

Handles queries like:
  - "Where is the water reservoir?"
  - "Highlight the airport runway"
  - "Find industrial areas in this scene"
  - "Locate rivers and water channels"
"""

import logging
import numpy as np
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _load_grounding_dino(checkpoint_path: str, device: str = "cpu"):
    """Load Grounding DINO 1.5 Edge model. Returns None if not available."""
    try:
        from groundingdino.util.inference import load_model, predict
        cfg_path = Path(checkpoint_path).parent / "gdino_1.5_edge_config.py"
        model = load_model(str(cfg_path), checkpoint_path, device=device)
        return model
    except Exception as e:
        logger.warning(f"Grounding DINO load failed: {e}")
        return None


def _load_mobile_sam(checkpoint_path: str, device: str = "cpu"):
    """Load MobileSAM v2 model. Returns None if not available."""
    try:
        from mobile_sam import sam_model_registry, SamPredictor
        sam = sam_model_registry["vit_t"](checkpoint=checkpoint_path)
        sam.to(device=device)
        sam.eval()
        return SamPredictor(sam)
    except Exception as e:
        logger.warning(f"MobileSAM load failed: {e}")
        return None


def run_grounding(
    image: np.ndarray,
    text_prompt: str,
    gdino_checkpoint: str = "models/grounding/gdino_1.5_edge.pth",
    sam_checkpoint: str = "models/segmentation/mobile_sam_v2.pt",
    box_threshold: float = 0.30,
    text_threshold: float = 0.25,
    device: str = "cpu"
) -> dict:
    """
    Run text-guided grounding pipeline:
      1. Grounding DINO → bounding boxes for text_prompt
      2. MobileSAM → pixel masks for each box
      
    Returns:
        dict with detections, masks, warnings, and is_stub flag.
    """
    warnings = []

    # --- Try Grounding DINO ---
    gdino_model = _load_grounding_dino(gdino_checkpoint, device)

    if gdino_model is None:
        logger.warning("Grounding DINO not available — returning stub.")
        return {
            "detections": [],
            "boxes": [],
            "scores": [],
            "masks": [],
            "fusion_method": "stub",
            "is_stub": True,
            "warnings": [
                "Grounding DINO not loaded. "
                "Install requirements_stage2.txt and download model weights to enable grounding.",
                f"Prompt was: '{text_prompt}'"
            ]
        }

    # --- Run detection ---
    try:
        from groundingdino.util.inference import predict
        from PIL import Image
        import torch

        # Convert numpy to PIL
        if image.dtype != np.uint8:
            image_uint8 = (image[:, :, :3] * 255).clip(0, 255).astype(np.uint8)
        else:
            image_uint8 = image[:, :, :3]

        pil_image = Image.fromarray(image_uint8)

        boxes, logits, phrases = predict(
            model=gdino_model,
            image=pil_image,
            caption=text_prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold
        )

        detections = []
        for box, score, phrase in zip(boxes.tolist(), logits.tolist(), phrases):
            detections.append({
                "box_xyxy": box,
                "score": round(score, 4),
                "label": phrase
            })

        # --- Run MobileSAM segmentation ---
        masks_list = []
        sam_predictor = _load_mobile_sam(sam_checkpoint, device)

        if sam_predictor is not None and detections:
            sam_predictor.set_image(image_uint8)
            for det in detections:
                box_np = np.array(det["box_xyxy"]).reshape(1, 4)
                masks, scores, _ = sam_predictor.predict(
                    box=box_np,
                    multimask_output=False
                )
                masks_list.append({
                    "label": det["label"],
                    "mask": masks[0].tolist(),
                    "score": float(scores[0])
                })
        else:
            if sam_predictor is None:
                warnings.append("MobileSAM not loaded — masks not generated. Bounding boxes only.")

        return {
            "detections": detections,
            "boxes": [d["box_xyxy"] for d in detections],
            "scores": [d["score"] for d in detections],
            "masks": masks_list,
            "n_detections": len(detections),
            "prompt": text_prompt,
            "fusion_method": "grounding_dino_1.5_edge + mobile_sam_v2",
            "is_stub": False,
            "warnings": warnings
        }

    except Exception as e:
        logger.error(f"Grounding pipeline error: {e}")
        return {
            "detections": [],
            "boxes": [],
            "scores": [],
            "masks": [],
            "fusion_method": "error",
            "is_stub": True,
            "warnings": [f"Grounding pipeline error: {str(e)[:200]}"]
        }
