import rasterio
import numpy as np
import cv2
import math
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RasterMetadata:
    width: int
    height: int
    count: int
    dtype: str
    crs: str | None
    crs_epsg: int | None
    transform: list[float]
    bounds: dict
    resolution_x: float
    resolution_y: float
    gsd_m: float | None
    nodata: float | None
    file_size_bytes: int
    format: str
    driver: str
    is_geographic: bool
    warnings: list[str]

def load_raster(path: Path) -> tuple[np.ndarray, RasterMetadata]:
    warnings = []
    try:
        with rasterio.open(path) as src:
            array = src.read()
            array = np.moveaxis(array, 0, -1)
            
            # Normalize to 0-1 if not float
            if 'float' not in str(src.profile['dtype']):
                max_val = np.iinfo(src.profile['dtype']).max if 'int' in str(src.profile['dtype']) else 255.0
                array = array.astype(np.float32) / max_val
            
            epsg = src.crs.to_epsg() if src.crs else None
            crs_str = str(src.crs) if src.crs else None
            is_geo = src.crs.is_geographic if src.crs else False
            
            bounds = {
                'left': src.bounds.left,
                'bottom': src.bounds.bottom,
                'right': src.bounds.right,
                'top': src.bounds.top
            }
            
            meta = RasterMetadata(
                width=src.width,
                height=src.height,
                count=src.count,
                dtype=str(src.profile['dtype']),
                crs=crs_str,
                crs_epsg=epsg,
                transform=list(src.transform)[:6],
                bounds=bounds,
                resolution_x=abs(src.transform.a),
                resolution_y=abs(src.transform.e),
                gsd_m=None,
                nodata=src.nodata,
                file_size_bytes=path.stat().st_size if path.exists() else 0,
                format=src.driver,
                driver=src.driver,
                is_geographic=is_geo,
                warnings=warnings
            )
            meta.gsd_m = estimate_gsd_meters(meta)
            if src.nodata is not None:
                warnings.append(f"Contains nodata value: {src.nodata}")
            return array, meta
    except Exception as e:
        raise ValueError(f"Failed to load raster {path}: {str(e)}")

def validate_raster(path: Path) -> tuple[bool, list[str]]:
    issues = []
    try:
        with rasterio.open(path) as src:
            if src.count < 1:
                issues.append("No bands found")
            if src.width == 0 or src.height == 0:
                issues.append("Invalid dimensions")
        return len(issues) == 0, issues
    except Exception as e:
        return False, [str(e)]

def generate_preview(array: np.ndarray, metadata: RasterMetadata, output_path: Path, max_size: int = 512) -> Path:
    h, w, c = array.shape
    scale = min(max_size / w, max_size / h)
    
    if scale < 1:
        new_w, new_h = int(w * scale), int(h * scale)
        preview = cv2.resize(array, (new_w, new_h))
    else:
        preview = array.copy()
        
    if c >= 3:
        # Assuming RGB in first 3 bands
        img = (preview[:, :, :3] * 255).astype(np.uint8)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:
        img = (preview[:, :, 0] * 255).astype(np.uint8)
        
    cv2.imwrite(str(output_path), img)
    return output_path

def get_band_statistics(array: np.ndarray) -> list[dict]:
    stats = []
    for i in range(array.shape[2]):
        band = array[:, :, i]
        stats.append({
            'min': float(np.nanmin(band)),
            'max': float(np.nanmax(band)),
            'mean': float(np.nanmean(band)),
            'std': float(np.nanstd(band)),
            'valid_pixels': int(np.count_nonzero(~np.isnan(band)))
        })
    return stats

def estimate_gsd_meters(metadata: RasterMetadata) -> float | None:
    if not metadata.is_geographic:
        return metadata.resolution_x
    
    lat = (metadata.bounds['top'] + metadata.bounds['bottom']) / 2
    # simple estimate based on latitude
    m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * math.radians(lat)) + 1.175 * math.cos(4 * math.radians(lat))
    return metadata.resolution_x * m_per_deg_lat
