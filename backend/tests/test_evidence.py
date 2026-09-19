from app.evidence.store import evidence_store
from app.evidence.schema import EvidenceRecord, EvidenceType
from datetime import datetime

def test_evidence_store():
    session_id = evidence_store.create_session()
    assert session_id in evidence_store.sessions
    
    record = EvidenceRecord(
        evidence_id="123",
        task="test",
        evidence_type=EvidenceType.DERIVED,
        source_image="img.tif",
        source_date=None,
        sensor=None,
        tool="test_tool",
        model=None,
        parameters={},
        result={},
        confidence=0.9,
        confidence_basis=None,
        geometry=None,
        timestamp=datetime.utcnow(),
        warnings=[]
    )
    
    evidence_store.add_evidence(session_id, record)
    fetched = evidence_store.get_evidence("123")
    assert fetched is not None
    assert fetched.evidence_id == "123"
