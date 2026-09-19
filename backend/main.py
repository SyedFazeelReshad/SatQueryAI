"""
Root entrypoint forwarder for SatQuery AI FastAPI backend.
Allows running with: uvicorn main:app
"""

from app.main import app

__all__ = ["app"]
