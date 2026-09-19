import numpy as np
from app.geospatial.area import region_percentage, scene_area_km2
from app.geospatial.raster import RasterMetadata

def test_region_percentage():
    mask = np.zeros((10, 10), dtype=bool)
    mask[:5, :] = True
    assert region_percentage(mask) == 50.0

def test_scene_area_km2():
    meta = RasterMetadata(
        width=100, height=100, count=1, dtype='float32',
        crs=None, crs_epsg=None, transform=[], bounds={},
        resolution_x=10, resolution_y=10, gsd_m=10.0,
        nodata=None, file_size_bytes=100, format='GTiff',
        driver='GTiff', is_geographic=False, warnings=[]
    )
    area = scene_area_km2(meta)
    # 100*100 pixels = 10000 pixels. 10m GSD -> 100m2 per pixel.
    # Total area = 1,000,000 m2 = 1.0 km2
    assert np.isclose(area, 1.0)
