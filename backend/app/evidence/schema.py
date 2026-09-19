from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid

class EvidenceType(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    DETECTED = "DETECTED"
    AI_DETECTED = "AI_DETECTED"
    INFERRED = "INFERRED"
    SYNTHETIC = "SYNTHETIC"

class EvidenceRecord(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    session_id: str | None = None
    task: str = "analysis"
    evidence_type: EvidenceType
    source_image: str = ""
    source: str | None = None
    source_date: str | None = None
    sensor: str | None = None
    tool: str
    model: str | None = None
    parameters: dict = Field(default_factory=dict)
    result: dict = Field(default_factory=dict)
    observation: str | None = None
    value: Any = None
    confidence: float | None = None
    confidence_basis: str | None = None
    geometry: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    warnings: list[str] = Field(default_factory=list)

    @property
    def id(self) -> str:
        return self.evidence_id

class EvidenceStore(BaseModel):
    session_id: str
    created_at: datetime
    records: list[EvidenceRecord]

class ConfidenceEstimate(BaseModel):
    score: float | None
    level: str
    basis: str
    signals: dict[str, float | str]
