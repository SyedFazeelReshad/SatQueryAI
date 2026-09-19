from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

class SatQueryError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class RasterLoadError(SatQueryError):
    pass

class ValidationError(SatQueryError):
    pass

class RegistrationError(SatQueryError):
    pass

class AnalysisError(SatQueryError):
    pass

class EvidenceNotFoundError(SatQueryError):
    pass

class ReportError(SatQueryError):
    pass

async def satquery_error_handler(request: Request, exc: SatQueryError):
    logger.error(f"SatQueryError: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "message": exc.message}
    )
