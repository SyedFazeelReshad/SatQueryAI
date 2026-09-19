#!/usr/bin/env python3
"""
SatQuery AI — Stage 1 Smoke Test
Verifies that backend and frontend are running correctly.
Run from the satquery-ai/ root directory.
"""

import sys
import time
import json
import os
import tempfile
from pathlib import Path
import numpy as np

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    import rasterio
    from rasterio.transform import from_origin
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

results = []


def check(name: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    print(f"  {status} {name}" + (f" -- {detail}" if detail else ""))
    results.append({"name": name, "passed": condition, "detail": detail})
    return condition


def section(title: str):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def create_sample_geotiff(path: Path) -> Path:
    """Create a valid 4-band GeoTIFF."""
    array = (np.random.rand(4, 64, 64) * 255).astype(np.uint8)
    # Synthetic pattern
    array[1, 10:30, 10:30] = 200 # green
    array[3, 10:30, 10:30] = 220 # NIR (veg)
    array[0, 35:55, 35:55] = 200 # blue
    
    transform = from_origin(77.5, 13.0, 0.0001, 0.0001)
    
    with rasterio.open(
        path, 'w', driver='GTiff',
        height=64, width=64, count=4, dtype='uint8',
        crs='EPSG:4326', transform=transform
    ) as dst:
        dst.write(array)
        
    return path


def main():
    print("\n" + "="*50)
    print("  SatQuery AI -- Stage 1 Smoke Test")
    print("="*50)
    print(f"\n  Backend: {BACKEND_URL}")
    print(f"  Frontend: {FRONTEND_URL}")
    
    # ---- 1. Backend Health ----
    section("1. Backend Health")
    try:
        r = httpx.get(f"{BACKEND_URL}/api/health", timeout=10)
        check("Backend reachable", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            check("Health status OK", data.get("status") == "ok", str(data.get("status")))
            check("Stage reported", "stage" in data, str(data.get("stage")))
            check("VLM status present", "vlm_available" in data)
            print(f"  {INFO} Stage: {data.get('stage')}, VLM: {data.get('vlm_available')}")
    except Exception as e:
        check("Backend reachable", False, str(e))
        print(f"\n  {WARN} Backend not running. Start with:")
        print("    cd backend && uvicorn app.main:app --reload --port 8000")
    
    # ---- 2. API Docs ----
    section("2. API Documentation")
    try:
        r = httpx.get(f"{BACKEND_URL}/docs", timeout=5)
        check("Swagger UI accessible", r.status_code == 200)
    except Exception as e:
        check("Swagger UI accessible", False, str(e))
    
    # ---- 3. GeoTIFF Upload & Analysis ----
    section("3. GeoTIFF Upload & Full Analysis")
    session_id = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        create_sample_geotiff(tmp_path)
        
        with open(tmp_path, "rb") as f:
            files = {"files": ("sample_scene.tif", f, "image/tiff")}
            data = {"query": "Describe the land cover and water bodies in this scene.", "mode": "single_image"}
            r = httpx.post(
                f"{BACKEND_URL}/api/analyze",
                files=files,
                data=data,
                timeout=60
            )
            
        if tmp_path.exists():
            tmp_path.unlink()
            
        check("Analyze endpoint response", r.status_code == 200, f"HTTP {r.status_code}")
        if r.status_code == 200:
            res = r.json()
            session_id = res.get("session_id")
            check("Session ID generated", bool(session_id), str(session_id))
            check("Task routed", "task_type" in res, str(res.get("task_type")))
            check("Measurements computed", len(res.get("measurements", [])) > 0, f"{len(res.get('measurements', []))} items")
            check("Confidence calculated", res.get("confidence") is not None, f"Score: {res.get('confidence')}")
            check("Evidence recorded", len(res.get("evidence_ids", [])) > 0, f"{len(res.get('evidence_ids', []))} IDs")
            check("Execution trace generated", bool(res.get("execution_trace_id")))
            check("Reports generated", bool(res.get("report_urls")), str(res.get("report_urls")))
            print(f"  {INFO} Answer preview:\n    {res.get('answer')[:120]}...")
    except Exception as e:
        check("GeoTIFF analysis execution", False, str(e))
    
    # ---- 4. Reports & Evidence Retrieval ----
    section("4. Reports & Evidence Endpoints")
    if session_id:
        try:
            r_json = httpx.get(f"{BACKEND_URL}/api/reports/{session_id}?format=json", timeout=5)
            check("Download JSON Report", r_json.status_code == 200)
            
            r_md = httpx.get(f"{BACKEND_URL}/api/reports/{session_id}?format=markdown", timeout=5)
            check("Download Markdown Report", r_md.status_code == 200)
        except Exception as e:
            check("Report endpoints", False, str(e))
    else:
        print(f"  {WARN} Skipping report retrieval tests (no session ID).")
    
    # ---- 5. Frontend Check ----
    section("5. Frontend Accessibility")
    try:
        r = httpx.get(FRONTEND_URL, timeout=10)
        check("Frontend reachable", r.status_code == 200, f"HTTP {r.status_code}")
        check("Contains SatQuery AI branding", "SatQuery" in r.text or "satquery" in r.text.lower())
    except Exception as e:
        check("Frontend reachable", False, str(e))
        print(f"\n  {WARN} Frontend not running. Start with:")
        print("    cd frontend && npm run dev")
    
    # ---- Summary ----
    section("Summary")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    failed = total - passed
    
    print(f"\n  Total Checks: {total}")
    print(f"  Passed:       {passed}")
    print(f"  Failed:       {failed}")
    
    if failed == 0:
        print(f"\n  All Stage 1 smoke tests passed successfully!\n")
    else:
        print(f"\n  Warning: {failed} test(s) failed. Check output above.\n")
        
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
