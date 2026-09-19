from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import analyze, query, evidence, reports, investigate
from app.core.config import settings
from app.core.errors import SatQueryError, satquery_error_handler
from app.models.responses import HealthResponse
from app.vision.model_loader import get_vlm, initialize_vlm_from_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Attempt to load Stage 2 VLM adapter if configured and present
    # Check parent directory or local relative path for configs/models.yaml
    config_paths = [
        Path("configs/models.yaml"),
        Path("../configs/models.yaml"),
        Path(__file__).resolve().parent.parent.parent / "configs" / "models.yaml"
    ]
    for cp in config_paths:
        if cp.exists():
            initialize_vlm_from_config(str(cp))
            break
    yield


app = FastAPI(
    title="SatQuery AI",
    description="Agentic Vision-Language Assistant for Remote Sensing",
    version="1.3.0-stage3",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(SatQueryError, satquery_error_handler)

settings.output_dir.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")

app.include_router(analyze.router)
app.include_router(query.router)
app.include_router(evidence.router)
app.include_router(reports.router)
app.include_router(investigate.router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    vlm = get_vlm()
    return HealthResponse(
        status="ok",
        version=app.version,
        stage=vlm.stage,
        vlm_available=vlm.is_available(),
        timestamp=datetime.utcnow().isoformat()
    )
