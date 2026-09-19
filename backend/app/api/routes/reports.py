from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.models.responses import AnalysisResult
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/results/{session_id}", response_model=AnalysisResult)
async def get_result(session_id: str):
    """Retrieve a completed analysis result by session ID."""
    from app.services.analysis_service import get_cached_result
    result = get_cached_result(session_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Result for session '{session_id}' not found. The server may have restarted. Please re-run analysis."
        )
    return result


@router.get("/reports/{session_id}")
async def get_report(session_id: str, format: str = "json"):
    path = settings.output_dir / f"report_{session_id}.{format}"
    if format == 'markdown':
        path = settings.output_dir / f"report_{session_id}.md"
    if path.exists():
        return FileResponse(path)
    return {"error": "Report not found"}


# Alias without 's' — some frontend versions call /api/report/ instead of /api/reports/
@router.get("/report/{session_id}")
async def get_report_alias(session_id: str, format: str = "json"):
    return await get_report(session_id, format)

