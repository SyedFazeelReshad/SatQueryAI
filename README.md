# SatQuery AI

> **SIH26167 — Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis**
> Organisation: ISRO | Domain: Space Technology / Software

SatQuery AI is a web-based agentic vision-language assistant that lets non-expert users upload satellite imagery and ask questions using natural language. The system automatically selects appropriate remote-sensing tools and AI models, executes them, and returns evidence-grounded answers with visual results.

---

## Architecture Overview

```
USER
 │
 ▼
NATURAL LANGUAGE QUERY
 │
 ▼
AGENT / ROUTER (software logic)
 │
 ┌──────────┼───────────┐
 ▼          ▼           ▼
VLM     GEO TOOLS   VISION TOOLS
 │          │           │
 └──────────┼───────────┘
            ▼
      EVIDENCE ENGINE
            │
            ▼
       CONFIDENCE ENGINE
            │
            ▼
       GROUNDED ANSWER
            │
     ┌──────┴──────┐
     ▼             ▼
VISUAL EVIDENCE   REPORT
```

---

## Development Stages

| Stage | Status | Description |
|-------|--------|-------------|
| **Stage 1** | ✅ Complete | Foundation — raster processing, classical analysis, evidence, API, frontend |
| **Stage 2** | ⏳ Pending | VLM Adaptation — LoRA fine-tuning on BigEarthNet |
| **Stage 3** | ⏳ Pending | Agentic AI — Grounding DINO, SAM2, full integration |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Remote Sensing | Rasterio, NumPy, SciPy, OpenCV, scikit-learn |
| AI/ML | PyTorch, Transformers, PEFT/LoRA |
| Models | Remote-sensing VLM (LoRA), Grounding DINO, SAM 2 |
| Infrastructure | Docker, Docker Compose |

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker + Docker Compose (optional)
- GDAL (for rasterio — see installation notes)

---

## Quick Start (Development)

### 1. Clone & Setup

```powershell
git clone <repo-url>
cd satquery-ai
Copy-Item .env.example .env
# Edit .env with your settings
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend available at: http://localhost:8000
API docs: http://localhost:8000/docs

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:3000

---

## Docker Compose

```powershell
docker compose -f infra/docker-compose.yml up --build
```

---

## Running Tests

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest tests/ -v
```

---

## Smoke Test

```powershell
python scripts/smoke_test.py
```

This verifies:
- Backend health endpoint responds
- GeoTIFF upload and metadata extraction work
- Basic analysis pipeline returns valid evidence

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/analyze` | POST | Main analysis (upload + query) |
| `/api/query` | POST | NL query against uploaded image |
| `/api/investigate` | POST | Advanced investigation workflow |
| `/api/evidence/{id}` | GET | Retrieve evidence record |
| `/api/reports/{id}` | GET | Download report |

Interactive API docs: http://localhost:8000/docs

---

## Stage 1 Capabilities

- ✅ GeoTIFF / TIFF upload and validation
- ✅ Raster metadata extraction (dims, bands, CRS, GSD, bounds, dtype)
- ✅ Raster preview generation
- ✅ NDVI (when NIR + Red bands available)
- ✅ NDWI (when Green + NIR bands available)
- ✅ Built-up proxy estimation
- ✅ Land-cover classification (K-Means + rule-based)
- ✅ Image registration (ORB + RANSAC)
- ✅ Change detection (CVA + Otsu + morphology)
- ✅ Change area calculation
- ✅ Optical + SAR feature extraction and fusion
- ✅ Evidence engine with confidence scoring
- ✅ Agentic router and tool registry
- ✅ JSON + Markdown reports
- ✅ Dark, professional web frontend

> **Note:** In Stage 1, the VLM returns clearly-labelled stub responses. All numerical measurements come from deterministic raster analysis only.

---

## Stage 2 — VLM Training (Pending)

Training will be performed on Google Colab GPU. See `training/` directory.

```powershell
# After training produces an adapter:
# Copy adapter to: models/trained/rs_vlm_lora/
# Update configs/models.yaml: adapter_path: models/trained/rs_vlm_lora/
# Set primary_vlm.stage: 2
```

---

## Project Structure

```
satquery-ai/
├── backend/          # FastAPI Python backend
├── frontend/         # Next.js TypeScript frontend
├── training/         # VLM training code (Stage 2)
├── models/           # Model checkpoints
├── data/             # Data (raw, processed, samples)
├── configs/          # Configuration YAML files
├── docs/             # Documentation
├── infra/            # Docker Compose, nginx
├── scripts/          # Setup and utility scripts
├── .env.example      # Environment variable template
└── README.md
```

---

## Scientific Honesty Policy

This system distinguishes between:
- **OBSERVED** — directly from imagery metadata
- **DERIVED** — calculated deterministically from raster data
- **DETECTED** — result of algorithmic detection
- **AI-DETECTED** — result of an AI model with confidence score
- **INFERRED** — hypothesis from evidence
- **SYNTHETIC** — artificial demonstration data

The system never fabricates measurements, detections, or analysis results.

---

## Limitations (Stage 1)

- VLM responses are stubs until Stage 2 training is complete
- Grounding DINO and SAM2 are not yet integrated (Stage 3)
- Change detection is classical (pixel-based), not deep learning
- Band assignment depends on correct metadata or user configuration
- Registration quality depends on image overlap and feature richness

---

## License

MIT License — see [LICENSE](LICENSE)
