import numpy as np
from app.geospatial.indices import calculate_ndvi, calculate_ndwi

def test_calculate_ndvi():
    array = np.zeros((10, 10, 4), dtype=np.float32)
    array[:, :, 2] = 0.1 # Red
    array[:, :, 3] = 0.5 # NIR
    
    res = calculate_ndvi(array, red_band=2, nir_band=3)
    # (0.5 - 0.1) / (0.5 + 0.1) = 0.4 / 0.6 = 0.666
    assert 'ndvi' in res
    assert np.isclose(res['mean'], 0.6666, atol=1e-3)
    
def test_calculate_ndwi():
    array = np.zeros((10, 10, 4), dtype=np.float32)
    array[:, :, 1] = 0.5 # Green
    array[:, :, 3] = 0.1 # NIR
    
    res = calculate_ndwi(array, green_band=1, nir_band=3)
    assert 'ndwi' in res
    assert np.isclose(res['mean'], 0.6666, atol=1e-3)
