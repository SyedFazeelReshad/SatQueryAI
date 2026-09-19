def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == "ok"
    assert data['stage'] == 1

def test_analyze_endpoint(client, synthetic_raster):
    with open(synthetic_raster, "rb") as f:
        response = client.post(
            "/api/analyze",
            data={"query": "find water classes", "mode": "single_image"},
            files=[("files", ("test_raster.tif", f, "image/tiff"))]
        )
    assert response.status_code == 200
    data = response.json()
    assert data['task_type'] == "single_landcover"
