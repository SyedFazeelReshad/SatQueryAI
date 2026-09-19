from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.responses import AnalysisResult
from app.models.requests import AnalysisMode
from app.services.analysis_service import run_analysis

router = APIRouter(prefix="/api", tags=["analysis"])

@router.post("/analyze", response_model=AnalysisResult)
async def analyze(
    query: str = Form(...),
    mode: str = Form(...),
    date_a: str | None = Form(None),
    date_b: str | None = Form(None),
    files: list[UploadFile] = File(...),
):
    try:
        req_mode = AnalysisMode(mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode")
        
    return await run_analysis(req_mode, files, query, {"date_a": date_a, "date_b": date_b})
