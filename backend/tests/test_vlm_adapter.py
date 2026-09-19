import numpy as np
import pytest
from app.vision.vlm_adapter import VLMAdapter
from app.vision.model_loader import get_vlm, QwenVLModelSingleton
from app.vision.grounding import run_grounding


def test_vlm_adapter_initialization():
    adapter = VLMAdapter({"max_new_tokens": 256})
    assert adapter is not None
    # In initial test environment (no adapter downloaded yet), is_available should be False
    assert adapter.is_available() is False


def test_vlm_adapter_answer_question():
    adapter = VLMAdapter({})
    dummy_img = np.random.rand(64, 64, 3).astype(np.float32)
    res = adapter.answer_question(dummy_img, "What land cover is visible?")
    assert "answer" in res
    assert "stage" in res
    assert "is_stub" in res
    assert res["is_stub"] is True  # Stub active until weights placed in models/


def test_vlm_adapter_generate_caption():
    adapter = VLMAdapter({})
    dummy_img = np.random.rand(64, 64, 3).astype(np.float32)
    res = adapter.generate_caption(dummy_img, {"measurements": [{"label": "NDVI", "value": 0.45}]})
    assert "caption" in res
    assert "is_stub" in res


def test_vlm_adapter_explain_change():
    adapter = VLMAdapter({})
    img_a = np.random.rand(64, 64, 3).astype(np.float32)
    img_b = np.random.rand(64, 64, 3).astype(np.float32)
    res = adapter.explain_change(img_a, img_b, {"change_percentage": 14.2, "question": "Why did area decrease?"})
    assert "answer" in res
    assert "stage" in res


def test_grounding_fallback():
    dummy_img = np.random.rand(64, 64, 3).astype(np.float32)
    res = run_grounding(dummy_img, "water reservoir")
    assert "detections" in res
    assert "boxes" in res
    assert "masks" in res
    assert res["is_stub"] is True


def test_vlm_singleton():
    v1 = get_vlm()
    v2 = get_vlm()
    assert v1 is v2
    assert isinstance(v1, QwenVLModelSingleton)
