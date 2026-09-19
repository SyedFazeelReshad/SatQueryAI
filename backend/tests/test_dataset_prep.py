import pytest
from pathlib import Path
import sys

# Ensure training module is accessible
training_dir = Path(__file__).parent.parent.parent / "training"
sys.path.insert(0, str(training_dir.parent))

from training.preprocessing.filtering import filter_patch_by_metadata, filter_patch_by_raster_quality, filter_dataset_manifest
from training.preprocessing.splitting import split_dataset
import numpy as np

def test_filter_patch_by_metadata_accepted():
    labels = ["Continuous urban fabric", "Water bodies"]
    meta = {"cloud_cover_percentage": 2.0, "snow_cover_percentage": 0.0}
    is_ok, reason = filter_patch_by_metadata("patch_1", labels, meta)
    assert is_ok is True
    assert reason == "ACCEPTED"

def test_filter_patch_by_metadata_rejected_cloudy():
    labels = ["Forest"]
    meta = {"cloud_cover_percentage": 25.0} # above 15% threshold
    is_ok, reason = filter_patch_by_metadata("patch_2", labels, meta)
    assert is_ok is False
    assert "CLOUDY" in reason

def test_filter_patch_by_metadata_rejected_uninformative_ocean():
    labels = ["Sea and ocean"]
    meta = {"cloud_cover_percentage": 0.0}
    is_ok, reason = filter_patch_by_metadata("patch_3", labels, meta, allow_pure_ocean=False)
    assert is_ok is False
    assert "UNINFORMATIVE" in reason

def test_filter_patch_by_raster_quality():
    good_img = np.random.rand(64, 64, 3).astype(np.float32)
    is_ok, reason = filter_patch_by_raster_quality(good_img)
    assert is_ok is True
    assert reason == "ACCEPTED"
    
    # All nan image
    bad_img = np.full((64, 64, 3), np.nan)
    is_ok, reason = filter_patch_by_raster_quality(bad_img)
    assert is_ok is False
    assert "NAN" in reason

def test_split_dataset():
    manifest = [{"patch_id": f"p_{i}", "labels": ["urban"]} for i in range(100)]
    train, val, test, meta = split_dataset(manifest, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
    assert len(train) == 80
    assert len(val) == 10
    assert len(test) == 10
    assert "manifest_hash" in meta
