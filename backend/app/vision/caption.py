import numpy as np
from app.vision.vlm_adapter import VLMAdapter

def run_captioning(image: np.ndarray, metadata, evidence: dict) -> dict:
    adapter = VLMAdapter({})
    return adapter.generate_caption(image, {'metadata': metadata, 'evidence': evidence})
