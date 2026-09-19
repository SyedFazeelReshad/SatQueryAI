"""
SatQuery AI — Demo Sample Generator (Stage 3)

Generates 4 realistic multi-band georeferenced GeoTIFF scenes for hackathon demonstration:
1. Delhi Urban Expansion (Bi-temporal Optical Pair: T1 vs T2)
2. Kerala Flood Inundation (Multimodal Optical + SAR Pair)
3. Sundarbans Mangrove Vegetation Health (4-band Optical with rich NDVI dynamics)
4. Jodhpur Solar Park Infrastructure (Grounding / Object Detection scenario)
"""

import os
import sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SAMPLE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)


def create_geotiff(
    filename: str,
    bands: list[np.ndarray],
    crs: str = "EPSG:32643",
    pixel_size: float = 10.0,
    origin_x: float = 500000.0,
    origin_y: float = 3100000.0
):
    """Save multi-band 2D numpy arrays into a georeferenced GeoTIFF."""
    out_path = SAMPLE_DIR / filename
    height, width = bands[0].shape
    count = len(bands)
    transform = from_origin(origin_x, origin_y, pixel_size, pixel_size)

    with rasterio.open(
        out_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=count,
        dtype=bands[0].dtype,
        crs=crs,
        transform=transform,
        nodata=0
    ) as dst:
        for idx, band in enumerate(bands, start=1):
            dst.write(band, idx)

    print(f"✅ Generated: {filename} ({width}x{height} px, {count} bands, {out_path.stat().st_size / 1024:.1f} KB)")
    return out_path


def generate_all_samples():
    print("🛰️ Generating SatQuery AI Stage 3 Demo Samples...\n")
    np.random.seed(42)
    H, W = 256, 256

    # ─────────────────────────────────────────────────────────────
    # Scenario 1: Delhi Urban Expansion (Bi-temporal Optical Pair)
    # Band Order: 1:Blue, 2:Green, 3:Red, 4:NIR
    # ─────────────────────────────────────────────────────────────
    # T1 (2021) - Mostly green agricultural land with small urban center
    t1_blue = np.random.normal(50, 8, (H, W)).clip(10, 255).astype(np.uint8)
    t1_green = np.random.normal(75, 10, (H, W)).clip(10, 255).astype(np.uint8)
    t1_red = np.random.normal(45, 8, (H, W)).clip(10, 255).astype(np.uint8)
    t1_nir = np.random.normal(160, 20, (H, W)).clip(10, 255).astype(np.uint8)
    # Add small urban center in top-left
    t1_blue[:80, :80] = 120
    t1_green[:80, :80] = 130
    t1_red[:80, :80] = 140
    t1_nir[:80, :80] = 90

    create_geotiff("delhi_urban_t1_2021.tif", [t1_blue, t1_green, t1_red, t1_nir])

    # T2 (2024) - Urban expansion: concrete expanded into central fields
    t2_blue = t1_blue.copy()
    t2_green = t1_green.copy()
    t2_red = t1_red.copy()
    t2_nir = t1_nir.copy()
    # Expansion zone in center-right
    t2_blue[80:180, 80:200] = 145
    t2_green[80:180, 80:200] = 150
    t2_red[80:180, 80:200] = 165
    t2_nir[80:180, 80:200] = 85

    create_geotiff("delhi_urban_t2_2024.tif", [t2_blue, t2_green, t2_red, t2_nir])

    # ─────────────────────────────────────────────────────────────
    # Scenario 2: Kerala Flood (Optical + SAR)
    # ─────────────────────────────────────────────────────────────
    # Optical: clouded in parts
    kerala_opt_b = np.random.normal(60, 10, (H, W)).clip(10, 255).astype(np.uint8)
    kerala_opt_g = np.random.normal(80, 12, (H, W)).clip(10, 255).astype(np.uint8)
    kerala_opt_r = np.random.normal(55, 10, (H, W)).clip(10, 255).astype(np.uint8)
    kerala_opt_nir = np.random.normal(170, 15, (H, W)).clip(10, 255).astype(np.uint8)
    create_geotiff("kerala_flood_optical.tif", [kerala_opt_b, kerala_opt_g, kerala_opt_r, kerala_opt_nir])

    # SAR: Sentinel-1 VV single-band backscatter (water is specular/dark ~ 20)
    sar_vv = np.random.normal(90, 15, (H, W)).clip(0, 255).astype(np.uint8)
    # Flooded water basin (dark in SAR)
    sar_vv[100:200, 60:190] = np.random.normal(25, 5, (100, 130)).clip(0, 255).astype(np.uint8)
    create_geotiff("kerala_flood_sar.tif", [sar_vv], crs="EPSG:32643")

    # ─────────────────────────────────────────────────────────────
    # Scenario 3: Sundarbans Mangrove Vegetation
    # Rich mangrove forest with river channels (NDVI demonstration)
    # ─────────────────────────────────────────────────────────────
    sb_blue = np.random.normal(40, 5, (H, W)).clip(10, 255).astype(np.uint8)
    sb_green = np.random.normal(90, 10, (H, W)).clip(10, 255).astype(np.uint8)
    sb_red = np.random.normal(35, 5, (H, W)).clip(10, 255).astype(np.uint8)
    sb_nir = np.random.normal(195, 15, (H, W)).clip(10, 255).astype(np.uint8)
    # Tidal river channel through middle
    for y in range(H):
        x_river = int(120 + 30 * np.sin(y / 20.0))
        sb_blue[y, max(0, x_river - 15):min(W, x_river + 15)] = 75
        sb_green[y, max(0, x_river - 15):min(W, x_river + 15)] = 65
        sb_red[y, max(0, x_river - 15):min(W, x_river + 15)] = 50
        sb_nir[y, max(0, x_river - 15):min(W, x_river + 15)] = 20  # Water absorbs NIR

    create_geotiff("sundarbans_mangrove.tif", [sb_blue, sb_green, sb_red, sb_nir])

    # ─────────────────────────────────────────────────────────────
    # Scenario 4: Jodhpur Solar Park (Grounding detection)
    # Solar panel arrays with regular geometric high-contrast patterns
    # ─────────────────────────────────────────────────────────────
    solar_b = np.random.normal(110, 10, (H, W)).clip(10, 255).astype(np.uint8)
    solar_g = np.random.normal(120, 10, (H, W)).clip(10, 255).astype(np.uint8)
    solar_r = np.random.normal(130, 10, (H, W)).clip(10, 255).astype(np.uint8)
    solar_nir = np.random.normal(140, 10, (H, W)).clip(10, 255).astype(np.uint8)
    # Solar panel arrays (dark blue/purple in optical, distinct bounding boxes)
    for r in range(3):
        for c in range(3):
            y0, y1 = 40 + r * 65, 85 + r * 65
            x0, x1 = 40 + c * 65, 85 + c * 65
            solar_b[y0:y1, x0:x1] = 40
            solar_g[y0:y1, x0:x1] = 45
            solar_r[y0:y1, x0:x1] = 35
            solar_nir[y0:y1, x0:x1] = 30

    create_geotiff("jodhpur_solar_park.tif", [solar_b, solar_g, solar_r, solar_nir])

    print("\n✨ All 4 demo scenarios successfully generated in data/samples/!")


if __name__ == "__main__":
    generate_all_samples()
