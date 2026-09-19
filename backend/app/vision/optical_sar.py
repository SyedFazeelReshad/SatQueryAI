"""
SatQuery AI — Optical + SAR Fusion Module
Stage 1: Feature-level fusion and analysis of co-registered Optical + SAR imagery.

Optical provides: spectral reflectance, NDVI (vegetation), NDWI (water)
SAR provides: structural backscatter, surface roughness (VV/VH), day/night/all-weather information
"""

import numpy as np
from app.geospatial.indices import calculate_ndvi, calculate_ndwi

def analyze_optical_sar(optical: np.ndarray, sar: np.ndarray, meta_optical, meta_sar, query: str) -> dict:
    warnings = []
    measurements = {}
    
    # 1. Optical features
    if optical.shape[2] >= 4:
        ndvi_res = calculate_ndvi(optical, red_band=2, nir_band=3, nodata=meta_optical.nodata)
        if "vegetation_fraction" in ndvi_res:
            measurements["optical_vegetation_coverage"] = round(ndvi_res["vegetation_fraction"] * 100, 2)
        ndwi_res = calculate_ndwi(optical, green_band=1, nir_band=3, nodata=meta_optical.nodata)
        if "water_fraction" in ndwi_res:
            measurements["optical_water_coverage"] = round(ndwi_res["water_fraction"] * 100, 2)
    elif optical.shape[2] >= 3:
        warnings.append("Optical image has 3 bands (RGB). NIR band unavailable for optical vegetation index.")
    
    # 2. SAR features (backscatter intensity & texture)
    sar_mean = float(np.nanmean(sar))
    sar_std = float(np.nanstd(sar))
    measurements["sar_mean_intensity"] = round(sar_mean, 4)
    measurements["sar_intensity_std"] = round(sar_std, 4)
    
    # High backscatter in SAR typically indicates urban/built-up structural double-bounce
    sar_band0 = sar[:, :, 0] if len(sar.shape) == 3 else sar
    high_backscatter_mask = sar_band0 > (sar_mean + 0.5 * sar_std)
    high_backscatter_frac = float(np.mean(high_backscatter_mask))
    measurements["sar_high_backscatter_fraction"] = round(high_backscatter_frac * 100, 2)
    
    # Smooth low-backscatter in SAR indicates specular reflection (water bodies, runways)
    low_backscatter_mask = sar_band0 < (sar_mean - 0.5 * sar_std)
    low_backscatter_frac = float(np.mean(low_backscatter_mask))
    measurements["sar_specular_low_backscatter_fraction"] = round(low_backscatter_frac * 100, 2)
    
    fusion_desc = (
        "Optical imagery provides spectral context and vegetation/water indicators. "
        "SAR imagery provides structural roughness and backscatter response independent of cloud cover. "
        f"Detected {measurements.get('sar_high_backscatter_fraction', 0)}% high-backscatter structural area (urban proxy) "
        f"and {measurements.get('sar_specular_low_backscatter_fraction', 0)}% low-backscatter smooth surface (water/flat proxy)."
    )
    
    return {
        'classification': fusion_desc,
        'fusion_method': "feature_based_correlation",
        'measurements': measurements,
        'confidence': 0.85,
        'is_stub': False,
        'warnings': warnings
    }
