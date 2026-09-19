from fastapi import APIRouter, HTTPException
from app.evidence.store import evidence_store

router = APIRouter(prefix="/api", tags=["evidence"])

@router.get("/evidence/{evidence_id}")
async def get_evidence(evidence_id: str):
    record = evidence_store.get_evidence(evidence_id)
    if not record:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return record
