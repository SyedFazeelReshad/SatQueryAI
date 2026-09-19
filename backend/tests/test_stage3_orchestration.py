"""
Tests for Stage 3 Agentic Orchestrator and Follow-Up Endpoints.
"""

import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.agents.orchestrator import AgentOrchestrator
from app.agents.planner import create_plan
from app.agents.router import RouterResult, TaskType, InputConfig
from app.agents.registry import tool_registry
from app.geospatial.raster import RasterMetadata
from app.evidence.store import evidence_store
from app.evidence.schema import EvidenceRecord, EvidenceType


@pytest.fixture
def mock_metadata():
    return RasterMetadata(
        width=64,
        height=64,
        count=4,
        dtype="uint8",
        crs="EPSG:32643",
        crs_epsg=32643,
        transform=[10.0, 0.0, 500000.0, 0.0, -10.0, 3000000.0],
        bounds={"left": 500000.0, "bottom": 2999360.0, "right": 500640.0, "top": 3000000.0},
        resolution_x=10.0,
        resolution_y=10.0,
        gsd_m=10.0,
        nodata=None,
        file_size_bytes=16384,
        format="GTiff",
        driver="GTiff",
        is_geographic=False,
        warnings=[]
    )


def test_tool_registry_loads_yaml():
    yaml_path = Path("../configs/tools.yaml")
    if not yaml_path.exists():
        yaml_path = Path("configs/tools.yaml")
    
    if yaml_path.exists():
        tool_registry.load_from_yaml(yaml_path)
        assert len(tool_registry.tools) > 0
        assert "ndvi" in tool_registry.tools or "NDVI Calculator" in tool_registry.tools


def test_orchestrator_single_image_vqa(mock_metadata, tmp_path):
    orchestrator = AgentOrchestrator(output_dir=tmp_path)
    
    input_cfg = InputConfig(n_images=1, modalities=["optical"], has_temporal_info=False)
    router_res = RouterResult(
        task_type=TaskType.SINGLE_VQA,
        confidence=0.9,
        reasoning="Test single image query",
        suggested_tools=["ndvi", "vqa"],
        input_config=input_cfg
    )
    plan = create_plan(router_res, input_cfg)
    
    # 64x64 4-band image (Blue, Green, Red, NIR)
    image = np.ones((64, 64, 4), dtype=np.uint8) * 100
    image[:, :, 3] = 180  # high NIR
    
    result = orchestrator.run(
        plan=plan,
        router_result=router_res,
        session_id="test_sess_001",
        query="What is the vegetation status?",
        image_a=image,
        image_b=None,
        meta_a=mock_metadata,
        meta_b=None
    )
    
    assert result.session_id == "test_sess_001"
    assert len(result.measurements) > 0
    assert result.confidence is not None
    assert result.trace_id != ""


def test_orchestrator_change_detection(mock_metadata, tmp_path):
    orchestrator = AgentOrchestrator(output_dir=tmp_path)
    
    input_cfg = InputConfig(n_images=2, modalities=["optical", "optical"], has_temporal_info=True)
    router_res = RouterResult(
        task_type=TaskType.CHANGE_DETECTION,
        confidence=0.95,
        reasoning="Test change query",
        suggested_tools=["image_registration", "change_detection", "area_calculator"],
        input_config=input_cfg
    )
    plan = create_plan(router_res, input_cfg)
    
    img_a = np.ones((64, 64, 4), dtype=np.uint8) * 100
    img_b = np.ones((64, 64, 4), dtype=np.uint8) * 100
    img_b[20:40, 20:40, :] = 220  # changed patch
    
    result = orchestrator.run(
        plan=plan,
        router_result=router_res,
        session_id="test_sess_002",
        query="Detect urban growth between dates",
        image_a=img_a,
        image_b=img_b,
        meta_a=mock_metadata,
        meta_b=mock_metadata
    )
    
    assert result.session_id == "test_sess_002"
    # Changed area measurement should be present
    labels = [m["label"] for m in result.measurements]
    assert "Changed Area" in labels
    assert "change" in result.layers


def test_followup_query_api():
    client = TestClient(app)
    
    # Pre-populate evidence for a session
    sess_id = "test_sess_api_01"
    rec = EvidenceRecord(
        evidence_id="ev_test_1",
        session_id=sess_id,
        task="ndvi_analysis",
        evidence_type=EvidenceType.DERIVED,
        tool="ndvi",
        observation="NDVI vegetation fraction is 45.2%",
        value={"vegetation_fraction": 0.452, "mean": 0.38}
    )
    evidence_store.add(sess_id, rec)
    
    resp = client.post("/api/query", json={
        "session_id": sess_id,
        "query": "Is there significant vegetation in this area?"
    })
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sess_id
    assert "answer" in data
    assert len(data["answer"]) > 0


def test_investigate_api():
    client = TestClient(app)
    
    sess_id = "test_sess_api_02"
    rec = EvidenceRecord(
        evidence_id="ev_test_2",
        session_id=sess_id,
        task="landcover",
        evidence_type=EvidenceType.DERIVED,
        tool="landcover_kmeans",
        observation="Detected 3 clusters: vegetation, water, urban",
        value={"classes": ["vegetation", "water", "urban"]}
    )
    evidence_store.add(sess_id, rec)
    
    resp = client.post("/api/investigate", json={
        "session_id": sess_id,
        "region_label": "dense_vegetation",
        "query": "What are the spectral properties of this cluster?"
    })
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sess_id
    assert "answer" in data
    assert "spectral_stats" in data
