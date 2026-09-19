import numpy as np
import cv2
from app.geospatial.raster import RasterMetadata
from app.geospatial.registration import register_images

def image_difference(array_a: np.ndarray, array_b: np.ndarray) -> np.ndarray:
    return np.abs(array_b.astype(np.float32) - array_a.astype(np.float32))

def change_vector_magnitude(diff: np.ndarray) -> np.ndarray:
    return np.sqrt(np.sum(diff**2, axis=2))

def otsu_threshold(magnitude: np.ndarray) -> tuple[np.ndarray, float]:
    mag_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    thresh_val, mask = cv2.threshold(mag_norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Map threshold value back to original scale
    original_thresh = (thresh_val / 255.0) * (magnitude.max() - magnitude.min()) + magnitude.min()
    return mask > 0, float(original_thresh)

def percentile_threshold(magnitude: np.ndarray, percentile: float = 95.0) -> tuple[np.ndarray, float]:
    thresh_val = np.percentile(magnitude, percentile)
    return magnitude > thresh_val, float(thresh_val)

def clean_change_mask(mask: np.ndarray, kernel_size: int = 3, min_area: int = 5) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    cleaned = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
    
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
    final_mask = np.zeros_like(cleaned)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            final_mask[labels == i] = 1
            
    return final_mask > 0

def compute_transition_matrix(class_map_a: np.ndarray, class_map_b: np.ndarray, classes: list[str]) -> dict:
    n_classes = len(classes)
    matrix = np.zeros((n_classes, n_classes), dtype=int)
    for i in range(n_classes):
        for j in range(n_classes):
            matrix[i, j] = np.sum((class_map_a == i) & (class_map_b == j))
            
    return {
        'matrix': matrix.tolist(),
        'classes': classes
    }

def perform_change_detection(array_a: np.ndarray, array_b: np.ndarray, meta_a: RasterMetadata, meta_b: RasterMetadata) -> dict:
    warnings = []
    
    reg_result = register_images(array_a, array_b)
    if not reg_result['success']:
        warnings.append("Registration failed, change detection may be inaccurate.")
        registered_b = array_b
    else:
        registered_b = reg_result['registered']
        if reg_result['quality_score'] < 0.5:
            warnings.append("Registration quality score is low.")
            
    diff = image_difference(array_a, registered_b)
    mag = change_vector_magnitude(diff)
    
    mask, thresh_val = percentile_threshold(mag, 95.0)
    cleaned_mask = clean_change_mask(mask)
    
    changed_pixels = int(np.sum(cleaned_mask))
    total_pixels = cleaned_mask.size
    
    return {
        'change_mask': cleaned_mask,
        'change_magnitude': mag,
        'change_percentage': float(changed_pixels / total_pixels) * 100 if total_pixels > 0 else 0.0,
        'changed_pixels': changed_pixels,
        'threshold_value': thresh_val,
        'threshold_method': 'percentile_95',
        'method': 'CVA',
        'warnings': warnings
    }
