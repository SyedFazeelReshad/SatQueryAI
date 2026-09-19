"""
SatQuery AI — Follow-up Query Endpoint (Stage 3)
Enables conversational exploration of an existing analysis session.
"""

from fastapi import APIRouter, HTTPException
import logging

from app.models.requests import QueryRequest
from app.models.responses import QueryResponse
from app.evidence.store import evidence_store
from app.vision.vlm_adapter import VLMAdapter

router = APIRouter(prefix="/api", tags=["query"])
logger = logging.getLogger(__name__)
_vlm = VLMAdapter({})


@router.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    """
    Interactive follow-up query on an existing analysis session.
    Uses stored evidence context + Qwen2-VL to answer the question.
    """
    session_id = request.session_id
    query = request.query

    # Retrieve evidence collected during the original analysis
    session_evidence = evidence_store.get_by_session(session_id)
    if not session_evidence:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Please run /api/analyze first."
        )

    # Build measurement context from stored evidence
    measurements = []
    for ev in session_evidence:
        if isinstance(ev.value, dict):
            for k, v in ev.value.items():
                if isinstance(v, (int, float)):
                    measurements.append({
                        "label": k.replace("_", " ").title(),
                        "value": round(v, 4),
                        "unit": "",
                        "evidence_type": ev.evidence_type.value
                    })

    # Use VLM to answer the query with context (no image in follow-up)
    logger.info(f"Follow-up query for session {session_id}: '{query}'")

    if not _vlm.is_available():
        answer = (
            f"[Stage 1 Mode] Follow-up query received: '{query}'. "
            f"Install Stage 2 VLM dependencies and LoRA adapter to enable contextual answers. "
            f"Evidence records available: {len(session_evidence)} observations from deterministic analysis."
        )
        return QueryResponse(
            session_id=session_id,
            query=query,
            answer=answer,
            model="stub",
            stage=1,
            is_stub=True,
            warnings=["VLM not available — stub answer returned."]
        )

    # Build context-rich prompt for follow-up
    evidence_lines = []
    for ev in session_evidence[:8]:
        obs = ev.observation or str(ev.result) if ev.result else ""
        if obs:
            evidence_lines.append(f"  - {ev.tool}: {obs[:120]}")
    evidence_summary = "\n".join(evidence_lines)

    # Check cached analysis result to access clean measurements
    from app.services.analysis_service import get_cached_result, _smart_answer_from_measurements
    cached_res = get_cached_result(session_id)
    cached_measurements = cached_res.measurements if cached_res else []

    # Check if GPU VLM is available
    from app.vision.model_loader import get_vlm
    vlm_singleton = get_vlm()

    if vlm_singleton.is_available() and getattr(vlm_singleton, 'device', 'cpu') != 'cpu':
        prompt = (
            f"You are SatQuery AI, a remote sensing analysis assistant.\n\n"
            f"Previous analysis evidence for this satellite scene:\n{evidence_summary}\n\n"
            f"User follow-up question: {query}\n\n"
            f"Answer accurately based on the evidence above. "
            f"Do not fabricate values not present in the evidence."
        )
        try:
            answer = vlm_singleton.infer(images=[], prompt=prompt, max_new_tokens=200, temperature=0.1)
        except Exception as e:
            logger.warning(f"VLM inference error in follow-up query: {e}")
            answer = _smart_answer_from_measurements(query, cached_measurements, type("MockMeta", (), {"width":0,"height":0,"count":3,"gsd_m":None,"crs":None}))
    else:
        # CPU fast path: generate smart deterministic answer from recorded measurements
        mock_meta = type("MockMeta", (), {"width": 0, "height": 0, "count": 3, "gsd_m": None, "crs": None})()
        if cached_measurements:
            answer = _smart_answer_from_measurements(query, cached_measurements, mock_meta)
        else:
            answer = f"Based on analysis evidence:\n{evidence_summary}\n\nQuery: {query}"

    return QueryResponse(
        session_id=session_id,
        query=query,
        answer=answer,
        model=f"SatQuery Intelligence (Stage {_vlm._stage()})",
        stage=_vlm._stage(),
        is_stub=False,
        warnings=[]
    )
