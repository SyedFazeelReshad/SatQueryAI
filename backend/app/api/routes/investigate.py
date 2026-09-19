"""
SatQuery AI — Deep Investigation Endpoint (Stage 3)
Targets a specific detected region or feature for deep spectral analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import numpy as np

from app.models.responses import InvestigateResponse
from app.evidence.store import evidence_store
from app.evidence.schema import EvidenceRecord, EvidenceType
from app.vision.vlm_adapter import VLMAdapter

router = APIRouter(prefix="/api", tags=["investigate"])
logger = logging.getLogger(__name__)
_vlm = VLMAdapter({})


class InvestigateRequest(BaseModel):
    session_id: str
    region_label: str = "detected_region"
    query: str = "What can you tell me about this specific region?"
    box_xyxy: list[float] | None = None    # Optional focus bounding box


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(request: InvestigateRequest):
    """
    Deep-dive investigation into a specific region or detected feature.
    Uses stored evidence context and VLM reasoning for targeted analysis.
    """
    session_evidence = evidence_store.get_by_session(request.session_id)
    if not session_evidence:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{request.session_id}' not found. Run /api/analyze first."
        )

    # Collect spectral stats from stored evidence
    spectral_stats = {}
    for ev in session_evidence:
        if isinstance(ev.value, dict) and ev.tool in ("ndvi", "ndwi", "landcover_kmeans"):
            spectral_stats[ev.tool] = ev.value

    region_focus = f"in the region labeled '{request.region_label}'"
    if request.box_xyxy:
        x0, y0, x1, y1 = request.box_xyxy
        region_focus = f"in the bounding box region [{x0:.0f},{y0:.0f}] to [{x1:.0f},{y1:.0f}]"

    evidence_summary = "\n".join([
        f"  - {ev.tool}: {ev.observation[:100]}"
        for ev in session_evidence[:6]
    ])

    if not _vlm.is_available():
        answer = (
            f"[Stage 1 Mode] Deep investigation {region_focus}. "
            f"Spectral data collected: {len(spectral_stats)} indices. "
            f"Deploy Stage 2 VLM to enable semantic region reasoning."
        )
    else:
        prompt = (
            f"You are SatQuery AI, a remote sensing analyst.\n\n"
            f"Analysis evidence:\n{evidence_summary}\n\n"
            f"The user wants a deep investigation {region_focus}.\n"
            f"Query: {request.query}\n\n"
            f"Provide a focused, scientifically precise answer about this region."
        )
        try:
            from app.vision.model_loader import get_vlm
            vlm_singleton = get_vlm()
            answer = vlm_singleton.infer(images=[], prompt=prompt, max_new_tokens=350, temperature=0.1)
        except Exception as e:
            answer = f"Investigation of {region_focus} based on stored evidence: {evidence_summary[:300]}"

    # Store investigation as evidence
    rec = EvidenceRecord(
        session_id=request.session_id,
        evidence_type=EvidenceType.INFERRED,
        tool="investigate",
        source="interactive_session",
        observation=f"User investigated region: {request.region_label}. Query: {request.query[:100]}",
        value={"region": request.region_label, "query": request.query},
        confidence=0.75
    )
    evidence_store.add(rec)

    return InvestigateResponse(
        session_id=request.session_id,
        region_label=request.region_label,
        spectral_stats=spectral_stats,
        answer=answer,
        evidence_ids=[rec.id],
        warnings=[]
    )
