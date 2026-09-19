import numpy as np
from app.vision.vlm_adapter import VLMAdapter

def run_vqa(image: np.ndarray, question: str, metadata, evidence: dict) -> dict:
    adapter = VLMAdapter({})
    return adapter.answer_question(image, question, {'metadata': metadata, 'evidence': evidence})
