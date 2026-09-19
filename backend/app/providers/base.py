from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class ImageProvider(ABC):
    @abstractmethod
    async def fetch_image(self, identifier: str) -> Path:
        pass
        
    @abstractmethod
    def get_metadata(self, identifier: str) -> dict[str, Any]:
        pass
