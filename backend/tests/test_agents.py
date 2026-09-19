from app.agents.router import route_query, InputConfig, TaskType

def test_route_query_change():
    config = InputConfig(n_images=2, modalities=["optical"], has_temporal_info=True)
    res = route_query("what changed?", config)
    assert res.task_type == TaskType.CHANGE_VQA

def test_route_query_landcover():
    config = InputConfig(n_images=1, modalities=["optical"], has_temporal_info=False)
    res = route_query("show me the water classes", config)
    assert res.task_type == TaskType.SINGLE_LANDCOVER
