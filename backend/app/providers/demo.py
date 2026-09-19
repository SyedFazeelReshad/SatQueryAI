from pathlib import Path
from app.providers.base import ImageProvider
import numpy as np
import rasterio

class DemoProvider(ImageProvider):
    async def fetch_image(self, identifier: str) -> Path:
        path = Path(f"./outputs/{identifier}.tif")
        if not path.exists():
            array = np.random.rand(4, 100, 100).astype(np.float32)
            with rasterio.open(
                path, 'w', driver='GTiff',
                height=100, width=100, count=4, dtype=str(array.dtype)
            ) as dst:
                dst.write(array)
        return path
        
    def get_metadata(self, identifier: str) -> dict:
        return {'is_synthetic': True}
