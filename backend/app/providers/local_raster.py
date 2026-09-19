from pathlib import Path
from app.providers.base import ImageProvider
from app.core.config import settings

class LocalRasterProvider(ImageProvider):
    async def fetch_image(self, identifier: str) -> Path:
        path = settings.upload_dir / identifier
        if not path.exists():
            raise FileNotFoundError(f"Image {identifier} not found in uploads.")
        return path
        
    def get_metadata(self, identifier: str) -> dict:
        return {}
