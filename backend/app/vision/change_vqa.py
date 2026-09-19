import numpy as np
from app.vision.vlm_adapter import VLMAdapter

def run_change_vqa(image_a: np.ndarray, image_b: np.ndarray, question: str, change_evidence: dict) -> dict:
    adapter = VLMAdapter({})
    evidence_with_q = dict(change_evidence)
    evidence_with_q["question"] = question
    return adapter.explain_change(image_a, image_b, evidence_with_q)
