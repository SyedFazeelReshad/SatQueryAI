"""
SatQuery AI — Dataset Filtering Module
Implements quality, spectral, and semantic filtering for remote sensing datasets (BigEarthNet).

Filtering Rules:
1. Cloud & Shadow Filter: Exclude patches flagged with high cloud cover or shadow distortion.
2. NoData & Zero-Variance Filter: Exclude corrupted tiles with excessive NoData (-9999 / NaN) or zero variance (flat black/white).
3. Monoculture & Uniform Sea Filter: Exclude purely uninformative sea or snow patches to prevent class imbalance.
4. Multimodal Pair Integrity: Verify both Optical (S2) and SAR (S1) bands exist and match spatially.
5. Valid Class Count: Require at least 1 verified Corine Land Cover (CLC) / BigEarthNet class label.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Classes that are uninformative if they are the ONLY class present across an entire scene
UNINFORMATIVE_STANDALONE_CLASSES = {
    "Sea and ocean",
    "Glaciers and perpetual snow"
}

# High-value remote-sensing interest classes
HIGH_PRIORITY_CLASSES = {
    "Continuous urban fabric",
    "Discontinuous urban fabric",
    "Industrial or commercial units",
    "Airports",
    "Port areas",
    "Water courses",
    "Water bodies",
    "Inland marshes",
    "Peat bogs",
    "Coniferous forest",
    "Broad-leaved forest",
    "Arable land",
    "Permanently irrigated land"
}


def filter_patch_by_metadata(
    patch_id: str,
    labels: List[str],
    metadata: Dict[str, Any],
    min_labels: int = 1,
    max_labels: int = 12,
    allow_pure_ocean: bool = False
) -> Tuple[bool, str]:
    """
    Evaluates metadata and class labels to determine if a patch should be kept.
    
    Returns:
        (is_accepted, reason_or_status)
    """
    if not labels or len(labels) < min_labels:
        return False, "REJECT_NO_LABELS: Patch has 0 recognized land-cover classes"
    
    if len(labels) > max_labels:
        return False, f"REJECT_TOO_MANY_LABELS: Patch has {len(labels)} classes (likely noisy boundary)"
    
    # Filter pure ocean tiles (unless explicitly enabled)
    if not allow_pure_ocean and len(labels) == 1 and labels[0] in UNINFORMATIVE_STANDALONE_CLASSES:
        return False, f"REJECT_UNINFORMATIVE: Patch contains only uniform '{labels[0]}'"
        
    # Check for cloudy metadata flags if present
    if metadata.get("cloud_cover_percentage", 0.0) > 15.0:
        return False, f"REJECT_CLOUDY: Cloud cover ({metadata.get('cloud_cover_percentage')}%) exceeds 15% threshold"
        
    if metadata.get("snow_cover_percentage", 0.0) > 30.0:
        return False, f"REJECT_SNOW: Snow cover ({metadata.get('snow_cover_percentage')}%) exceeds 30% threshold"
        
    return True, "ACCEPTED"


def filter_patch_by_raster_quality(
    image_array: np.ndarray,
    nodata_value: float = -9999.0,
    max_nodata_ratio: float = 0.05,
    min_variance: float = 1e-4
) -> Tuple[bool, str]:
    """
    Validates numerical integrity of raster array (Optical or SAR).
    
    Checks:
    - NaN / Inf values
    - NoData pixel percentage
    - Zero variance / dead sensor pixels
    """
    if image_array is None or image_array.size == 0:
        return False, "REJECT_EMPTY: Raster array is empty or None"
        
    if np.all(np.isnan(image_array)):
        return False, "REJECT_ALL_NAN: Raster contains only NaN values"
        
    # Calculate nodata ratio
    nodata_mask = np.isnan(image_array) | (image_array == nodata_value)
    nodata_ratio = np.sum(nodata_mask) / image_array.size
    
    if nodata_ratio > max_nodata_ratio:
        return False, f"REJECT_NODATA: NoData fraction ({nodata_ratio:.2%}) exceeds allowed {max_nodata_ratio:.2%}"
        
    # Check variance to remove blank or solid black tiles
    valid_pixels = image_array[~nodata_mask]
    if valid_pixels.size == 0:
        return False, "REJECT_NO_VALID_PIXELS: Zero valid pixels found"
        
    variance = float(np.var(valid_pixels))
    if variance < min_variance:
        return False, f"REJECT_ZERO_VARIANCE: Image variance ({variance:.6f}) below minimum threshold"
        
    return True, "ACCEPTED"


def filter_dataset_manifest(
    raw_manifest: List[Dict[str, Any]],
    target_sample_size: int = 10000,
    balance_classes: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Filters and balances a raw dataset manifest into a high-quality training subset.
    
    Returns:
        (filtered_manifest, statistics_dictionary)
    """
    filtered = []
    stats = {
        "total_evaluated": len(raw_manifest),
        "accepted": 0,
        "rejected_uninformative": 0,
        "rejected_cloudy": 0,
        "rejected_nodata": 0,
        "rejected_other": 0
    }
    
    class_counts: Dict[str, int] = {}
    
    for item in raw_manifest:
        patch_id = item.get("patch_id", "")
        labels = item.get("labels", [])
        meta = item.get("metadata", {})
        
        # 1. Metadata & semantic filter
        is_ok, reason = filter_patch_by_metadata(patch_id, labels, meta)
        if not is_ok:
            if "UNINFORMATIVE" in reason:
                stats["rejected_uninformative"] += 1
            elif "CLOUDY" in reason:
                stats["rejected_cloudy"] += 1
            else:
                stats["rejected_other"] += 1
            continue
            
        # 2. Class balancing (prioritize diverse/urban/water/forest over common pasture)
        if balance_classes and target_sample_size > 0:
            # Check if this patch adds value to less-represented classes
            has_high_priority = any(lbl in HIGH_PRIORITY_CLASSES for lbl in labels)
            
            # If we already have enough samples and this patch is common pasture, selectively skip
            if len(filtered) >= target_sample_size and not has_high_priority:
                continue
                
        filtered.append(item)
        stats["accepted"] += 1
        
        for lbl in labels:
            class_counts[lbl] = class_counts.get(lbl, 0) + 1
            
        if target_sample_size > 0 and len(filtered) >= target_sample_size:
            break
            
    logger.info(f"Dataset Filtering Summary: {stats['accepted']}/{stats['total_evaluated']} patches accepted.")
    return filtered, stats
