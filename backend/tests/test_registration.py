import numpy as np
from app.geospatial.registration import register_images, check_compatibility
from app.geospatial.raster import RasterMetadata

def test_check_compatibility():
    meta_a = RasterMetadata(
        width=100, height=100, count=3, dtype="uint8", crs="EPSG:4326",
        crs_epsg=4326, transform=[0, 10, 0, 0, 0, -10], bounds={"left": 0, "bottom": 0, "right": 1000, "top": 1000},
        resolution_x=10.0, resolution_y=10.0, gsd_m=10.0, nodata=None, file_size_bytes=1000,
        format="GTiff", driver="GTiff", is_geographic=True, warnings=[]
    )
    meta_b = RasterMetadata(
        width=100, height=100, count=3, dtype="uint8", crs="EPSG:4326",
        crs_epsg=4326, transform=[0, 10, 0, 0, 0, -10], bounds={"left": 0, "bottom": 0, "right": 1000, "top": 1000},
        resolution_x=10.0, resolution_y=10.0, gsd_m=10.0, nodata=None, file_size_bytes=1000,
        format="GTiff", driver="GTiff", is_geographic=True, warnings=[]
    )
    compatible, issues = check_compatibility(meta_a, meta_b)
    assert compatible is True
    assert len(issues) == 0

def test_register_images_fallback():
    # Synthetic blank / random images where ORB might not find keypoints or matches
    img1 = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    img2 = (np.random.rand(64, 64, 3) * 255).astype(np.uint8)
    res = register_images(img1, img2)
    assert "registered" in res
    assert "warnings" in res
    assert "quality_score" in res
