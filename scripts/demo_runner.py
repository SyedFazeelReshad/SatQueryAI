"""
SatQuery AI — Interactive Stage 3 Presentation & Demo Runner

Submits realistic demo scenarios to the running SatQuery backend
and displays live multi-modal analysis results with deterministic measurements,
execution trace DAGs, and VLM contextual reasoning.
"""

import sys
import time
import requests
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def check_health():
    try:
        r = requests.get(f"{API_URL}/api/health", timeout=3)
        if r.status_code == 200:
            data = r.json()
            print(f"🛰️  SatQuery AI Backend Online | Stage: {data.get('stage')} | VLM Active: {data.get('vlm_available')}")
            return True
    except Exception:
        print("⚠️  Backend not reachable at http://localhost:8000. Start it with:")
        print("    cd backend && .\\.venv\\Scripts\\python -m uvicorn app.main:app --port 8000")
        return False
    return False


def run_scenario(name: str, mode: str, query: str, filenames: list[str], params: dict = None):
    print("\n" + "=" * 70)
    print(f"🚀 RUNNING SCENARIO: {name}")
    print(f"   Mode: {mode}")
    print(f"   Query: \"{query}\"")
    print("=" * 70)

    files = []
    for fn in filenames:
        fp = SAMPLE_DIR / fn
        if not fp.exists():
            print(f"❌ File {fp} not found. Run python data/samples/create_demo_samples.py first.")
            return
        files.append(('files', (fn, open(fp, 'rb'), 'image/tiff')))

    data = {
        'query': query,
        'mode': mode,
        **(params or {})
    }

    t0 = time.time()
    try:
        res = requests.post(f"{API_URL}/api/analyze", data=data, files=files, timeout=60)
        elapsed = time.time() - t0

        if res.status_code != 200:
            print(f"❌ Analysis failed ({res.status_code}): {res.text}")
            return

        result = res.json()
        print(f"\n✅ Completed in {elapsed:.2f}s | Session: {result.get('session_id')}")
        print(f"   Task Routed: {result.get('task_type')} | Confidence: {result.get('confidence')} ({result.get('confidence_level')})")

        print("\n📊 Deterministic Measurements:")
        for m in result.get('measurements', []):
            print(f"   • {m['label']}: {m['value']} {m['unit']}  [{m['evidence_type']}]")

        print("\n🧠 VLM Synthesized Explanation:")
        print("   " + "\n   ".join(result.get('answer', '').splitlines()))

        layers = result.get('layers', {})
        if layers:
            print("\n🗺️  Generated Layers:")
            for l_name, l_url in layers.items():
                print(f"   • {l_name}: {API_URL}{l_url}")

        reports = result.get('report_urls', {})
        if reports:
            print("\n📄 Downloadable Reports:")
            for r_fmt, r_url in reports.items():
                print(f"   • {r_fmt.upper()}: {API_URL}{r_url}")

    except Exception as e:
        print(f"❌ Error during execution: {e}")


def main():
    print("=" * 70)
    print("       SATQUERY AI — STAGE 3 HACKATHON DEMO RUNNER")
    print("=" * 70)

    if not check_health():
        sys.exit(1)

    scenarios = [
        {
            "name": "Delhi NCR Urban Expansion (Bi-temporal Change Detection)",
            "mode": "change_analysis",
            "query": "Quantify urban expansion and changed land area between 2021 and 2024",
            "files": ["delhi_urban_t1_2021.tif", "delhi_urban_t2_2024.tif"],
            "params": {"date_a": "2021-03-15", "date_b": "2024-03-20"}
        },
        {
            "name": "Sundarbans Mangrove Vegetation Health & Water Coverage",
            "mode": "single_image",
            "query": "Assess vegetation density and water channels using spectral indices",
            "files": ["sundarbans_mangrove.tif"],
            "params": {}
        },
        {
            "name": "Kerala Flood Inundation (Optical + SAR Cross-Modal Fusion)",
            "mode": "optical_sar",
            "query": "Compare optical and SAR imagery to identify flooded terrain under cloud cover",
            "files": ["kerala_flood_optical.tif", "kerala_flood_sar.tif"],
            "params": {}
        },
        {
            "name": "Jodhpur Solar Park Infrastructure Detection (Grounding)",
            "mode": "single_image",
            "query": "Locate and delineate solar panel array infrastructure",
            "files": ["jodhpur_solar_park.tif"],
            "params": {}
        },
    ]

    print("\nSelect a scenario to run:")
    for i, s in enumerate(scenarios, start=1):
        print(f"  [{i}] {s['name']}")
    print("  [A] Run All Scenarios")
    print("  [Q] Quit")

    choice = input("\nEnter choice (1-4, A, Q): ").strip().upper()

    if choice == "Q":
        return
    elif choice == "A":
        for s in scenarios:
            run_scenario(s["name"], s["mode"], s["query"], s["files"], s["params"])
    elif choice.isdigit() and 1 <= int(choice) <= len(scenarios):
        s = scenarios[int(choice) - 1]
        run_scenario(s["name"], s["mode"], s["query"], s["files"], s["params"])
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
