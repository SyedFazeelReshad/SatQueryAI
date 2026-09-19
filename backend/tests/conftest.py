import pytest
from fastapi.testclient import TestClient
import numpy as np
import rasterio
from rasterio.transform import from_origin
from pathlib import Path
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def synthetic_raster(temp_dir):
    path = temp_dir / "test_raster.tif"
    array = np.random.rand(4, 100, 100).astype(np.float32)
    transform = from_origin(0, 0, 10, 10) # 10m GSD
    
    with rasterio.open(
        path, 'w', driver='GTiff',
        height=100, width=100, count=4, dtype=str(array.dtype),
        crs='+proj=latlong', transform=transform
    ) as dst:
        dst.write(array)
        
    return path
