import numpy as np
from app.vision.optical_sar import analyze_optical_sar
from app.geospatial.raster import RasterMetadata

def test_analyze_optical_sar():
    opt = (np.random.rand(50, 50, 4) * 255).astype(np.uint8)
    sar = (np.random.rand(50, 50, 2) * 255).astype(np.uint8)
    meta_opt = RasterMetadata(
        width=50, height=50, count=4, dtype="uint8", crs="EPSG:32643",
        crs_epsg=32643, transform=[0, 10, 0, 0, 0, -10], bounds={"left": 0, "bottom": 0, "right": 500, "top": 500},
        resolution_x=10.0, resolution_y=10.0, gsd_m=10.0, nodata=None, file_size_bytes=1000,
        format="GTiff", driver="GTiff", is_geographic=False, warnings=[]
    )
    meta_sar = RasterMetadata(
        width=50, height=50, count=2, dtype="uint8", crs="EPSG:32643",
        crs_epsg=32643, transform=[0, 10, 0, 0, 0, -10], bounds={"left": 0, "bottom": 0, "right": 500, "top": 500},
        resolution_x=10.0, resolution_y=10.0, gsd_m=10.0, nodata=None, file_size_bytes=1000,
        format="GTiff", driver="GTiff", is_geographic=False, warnings=[]
    )
    res = analyze_optical_sar(opt, sar, meta_opt, meta_sar, "identify built-up and water")
    assert "measurements" in res
    assert "fusion_method" in res
