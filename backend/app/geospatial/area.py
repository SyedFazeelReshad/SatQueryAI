import numpy as np
from app.geospatial.raster import RasterMetadata

def pixel_area_m2(metadata: RasterMetadata) -> float | None:
    if metadata.gsd_m is not None:
        return metadata.gsd_m * metadata.gsd_m
    return None

def region_area_m2(mask: np.ndarray, metadata: RasterMetadata) -> float | None:
    p_area = pixel_area_m2(metadata)
    if p_area is not None:
        return int(np.sum(mask)) * p_area
    return None

def region_area_km2(mask: np.ndarray, metadata: RasterMetadata) -> float | None:
    area_m2 = region_area_m2(mask, metadata)
    if area_m2 is not None:
        return area_m2 / 1_000_000.0
    return None

def scene_area_km2(metadata: RasterMetadata) -> float | None:
    p_area = pixel_area_m2(metadata)
    if p_area is not None:
        total_pixels = metadata.width * metadata.height
        return (total_pixels * p_area) / 1_000_000.0
    return None

def region_percentage(mask: np.ndarray) -> float:
    if mask.size == 0:
        return 0.0
    return float(np.sum(mask) / mask.size) * 100.0

def area_summary(mask: np.ndarray, metadata: RasterMetadata, label: str) -> dict:
    return {
        'label': label,
        'area_m2': region_area_m2(mask, metadata),
        'area_km2': region_area_km2(mask, metadata),
        'percentage': region_percentage(mask),
        'pixel_count': int(np.sum(mask)),
        'warnings': [] if metadata.gsd_m is not None else ["Area metrics unavailable due to unknown GSD/CRS"]
    }
