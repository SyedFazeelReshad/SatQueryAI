import numpy as np
from app.geospatial.landcover import perform_landcover_analysis
from app.geospatial.raster import RasterMetadata

def test_landcover_analysis():
    array = np.random.rand(50, 50, 4).astype(np.float32)
    meta = RasterMetadata(
        width=50, height=50, count=4, dtype="float32", crs="EPSG:32643",
        crs_epsg=32643, transform=[0, 10, 0, 0, 0, -10], bounds={"left": 0, "bottom": 0, "right": 500, "top": 500},
        resolution_x=10.0, resolution_y=10.0, gsd_m=10.0, nodata=None, file_size_bytes=1000,
        format="GTiff", driver="GTiff", is_geographic=False, warnings=[]
    )
    res = perform_landcover_analysis(array, meta, n_clusters=4)
    assert "class_map" in res
    assert "class_percentages" in res
    assert "classes" in res
    assert len(res["classes"]) >= 4
