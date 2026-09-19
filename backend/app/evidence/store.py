import json
import uuid
from pathlib import Path
from datetime import datetime
from app.evidence.schema import EvidenceRecord, EvidenceStore
from app.core.config import settings
from app.core.errors import EvidenceNotFoundError

class EvidenceStoreManager:
    def __init__(self):
        self.sessions: dict[str, EvidenceStore] = {}
        self.storage_dir = settings.output_dir / "evidence"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = EvidenceStore(
            session_id=session_id,
            created_at=datetime.utcnow(),
            records=[]
        )
        return session_id

    def add_evidence(self, session_id: str, record: EvidenceRecord) -> None:
        if session_id not in self.sessions:
            self.sessions[session_id] = EvidenceStore(
                session_id=session_id,
                created_at=datetime.utcnow(),
                records=[]
            )
        self.sessions[session_id].records.append(record)

    def add(self, session_id_or_record, record=None) -> None:
        """Convenience alias: can take (session_id, record) or just (record) if record has session_id."""
        if record is None:
            # record was passed as first arg
            rec = session_id_or_record
            s_id = getattr(rec, "session_id", "default")
            self.add_evidence(s_id, rec)
        else:
            self.add_evidence(session_id_or_record, record)

    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        for session in self.sessions.values():
            for record in session.records:
                if record.evidence_id == evidence_id:
                    return record
        return None

    def get_session_evidence(self, session_id: str) -> list[EvidenceRecord]:
        if session_id in self.sessions:
            return self.sessions[session_id].records
        return []

    def get_by_session(self, session_id: str) -> list[EvidenceRecord]:
        """Convenience alias for get_session_evidence."""
        return self.get_session_evidence(session_id)

    def save_session(self, session_id: str) -> Path:
        if session_id not in self.sessions:
            raise EvidenceNotFoundError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        path = self.storage_dir / f"{session_id}.json"
        
        with open(path, "w") as f:
            f.write(session.model_dump_json(indent=2))
            
        return path

evidence_store = EvidenceStoreManager()
