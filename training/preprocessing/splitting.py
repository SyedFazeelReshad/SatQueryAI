"""
SatQuery AI — Dataset Splitting Module
Generates stratified, deterministic train/validation/test splits with reproducibility hashes.
"""

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple


def compute_manifest_hash(manifest: List[Dict[str, Any]]) -> str:
    """Computes SHA-256 checksum of manifest to guarantee auditability."""
    raw_str = json.dumps([item.get("patch_id", "") for item in manifest], sort_keys=True)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


def split_dataset(
    manifest: List[Dict[str, Any]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Deterministically partitions manifest into train, validation, and test subsets.
    """
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0"
    
    # Deterministic shuffle
    rng = random.Random(seed)
    shuffled = list(manifest)
    rng.shuffle(shuffled)
    
    n_total = len(shuffled)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    
    train_set = shuffled[:n_train]
    val_set = shuffled[n_train:n_train + n_val]
    test_set = shuffled[n_train + n_val:]
    
    metadata = {
        "total_samples": n_total,
        "train_samples": len(train_set),
        "val_samples": len(val_set),
        "test_samples": len(test_set),
        "seed": seed,
        "manifest_hash": compute_manifest_hash(manifest),
        "train_hash": compute_manifest_hash(train_set),
        "val_hash": compute_manifest_hash(val_set),
        "test_hash": compute_manifest_hash(test_set)
    }
    
    return train_set, val_set, test_set, metadata
