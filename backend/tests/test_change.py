import numpy as np
from app.geospatial.change import image_difference, change_vector_magnitude

def test_image_difference():
    a = np.ones((10, 10, 1), dtype=np.float32)
    b = np.full((10, 10, 1), 3.0, dtype=np.float32)
    diff = image_difference(a, b)
    assert np.all(diff == 2.0)

def test_change_vector_magnitude():
    diff = np.full((10, 10, 3), 2.0, dtype=np.float32)
    # sqrt(2^2 + 2^2 + 2^2) = sqrt(12) = 3.464
    mag = change_vector_magnitude(diff)
    assert np.allclose(mag, 3.4641, atol=1e-3)
