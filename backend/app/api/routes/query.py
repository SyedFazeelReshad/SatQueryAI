"""
SatQuery AI - Follow-up Query Endpoint
Enables conversational exploration with Multimodal Vision.
"""
import os
import logging
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.models.requests import QueryRequest
from app.models.responses import QueryResponse
from app.evidence.store import evidence_store
from app.services.analysis_service import get_cached_result, _smart_answer_from_measurements

router = APIRouter(prefix="/api", tags=["query"])
logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are SatQuery AI, an expert multimodal geospatial and satellite image analysis assistant. "
    "When a satellite or aerial image is provided, answer questions with direct visual grounding. "
    "Identify specific objects (such as vehicles, cars, houses, roads, driveways, trees) "
    "and state their exact spatial location (e.g., upper-right corner, parked on the driveway, bottom-left). "
    "Be direct and precise."
)

@router.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    session_id = request.session_id
    query = request.query

    session_evidence = evidence_store.get_by_session(session_id)
    cached_res = get_cached_result(session_id)

    if not session_evidence and not cached_res:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    cached_measurements = cached_res.measurements if cached_res else []
    pil_image = None
    candidate_paths = [
        Path(f"outputs/preview_{session_id}.png"),
        Path(f"outputs/preview_{session_id}.jpg"),
        Path(f"outputs/{session_id}.png"),
        Path(f"backend/outputs/preview_{session_id}.png"),
        Path(f"static/outputs/preview_{session_id}.png"),
    ]
    if cached_res and getattr(cached_res, "preview_url", None):
        candidate_paths.insert(0, Path(cached_res.preview_url.lstrip("/")))

    for p in candidate_paths:
        if p.exists():
            try:
                pil_image = Image.open(p).convert("RGB")
                break
            except Exception:
                pass

    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if genai and api_key and not api_key.startswith("YOUR_") and not api_key.startswith("AIzaSyAapki"):
        try:
            genai.configure(api_key=api_key)
            g_model = genai.GenerativeModel("gemini-1.5-flash")
            meas_items = [f"{m.label}: {m.value}" if hasattr(m, "label") else str(m) for m in cached_measurements]
            measurements_context = "\n".join(meas_items)
            prompt = f"{_SYSTEM_PROMPT}\n\nMeasurements Context:\n{measurements_context}\n\nQuestion: {query}"
            contents = [pil_image, prompt] if pil_image else [prompt]
            response = g_model.generate_content(contents)
            if response and response.text:
                return QueryResponse(
                    session_id=session_id,
                    query=query,
                    answer=response.text.strip(),
                    model="SatQuery Multimodal Vision (Gemini 1.5 Flash)",
                    stage=2,
                    is_stub=False,
                    warnings=[]
                )
        except Exception as e:
            logger.warning(f"Gemini call failed: {e}")

    mock_meta = type("MockMeta", (), {"width": 0, "height": 0, "count": 3, "gsd_m": None, "crs": None})()
    if cached_measurements:
        answer = _smart_answer_from_measurements(query, cached_measurements, mock_meta)
    else:
        answer = "Unable to inspect visual features for this session."

    return QueryResponse(
        session_id=session_id,
        query=query,
        answer=answer,
        model="SatQuery Rule Engine",
        stage=1,
        is_stub=False,
        warnings=[]
    )