from app.geospatial.raster import load_raster, validate_raster

def test_load_raster(synthetic_raster):
    array, meta = load_raster(synthetic_raster)
    assert array.shape == (100, 100, 4)
    assert meta.width == 100
    assert meta.height == 100
    assert meta.count == 4

def test_validate_raster(synthetic_raster):
    is_valid, issues = validate_raster(synthetic_raster)
    assert is_valid is True
    assert len(issues) == 0
