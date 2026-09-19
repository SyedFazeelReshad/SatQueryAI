from pydantic import BaseModel


class RasterInfo(BaseModel):
    width: int
    height: int
    count: int
    dtype: str
    crs: str | None
    crs_epsg: int | None
    transform: list[float]
    bounds: dict
    resolution_x: float
    resolution_y: float
    gsd_m: float | None
    nodata: float | None
    file_size_bytes: int
    format: str
    driver: str
    is_geographic: bool
    warnings: list[str]


class MeasurementResult(BaseModel):
    label: str
    value: float | str
    unit: str
    evidence_type: str


class DetectionResult(BaseModel):
    """A single text-guided object detection with optional polygon mask."""
    label: str
    score: float
    box_xyxy: list[float]                  # [x_min, y_min, x_max, y_max] in pixel coords
    polygon_points: list[list[float]] = []  # [[x, y], ...] polygon contour from MobileSAM


class AnalysisResult(BaseModel):
    session_id: str
    task_type: str
    answer: str
    measurements: list[MeasurementResult]
    confidence: float | None
    confidence_level: str
    evidence_ids: list[str]
    execution_trace_id: str
    warnings: list[str]
    preview_url: str | None
    overlay_url: str | None
    preview_b_url: str | None = None   # Second image preview for change analysis
    layers: dict[str, str] = {}       # layer_name → URL (e.g. "ndvi" → "/outputs/xxx_ndvi_layer.png")
    detections: list[DetectionResult] = []  # Grounding DINO + MobileSAM detections
    report_urls: dict[str, str]


class QueryResponse(BaseModel):
    """Response to a follow-up conversational query on an existing session."""
    session_id: str
    query: str
    answer: str
    model: str
    stage: int
    is_stub: bool
    warnings: list[str] = []


class InvestigateResponse(BaseModel):
    """Deep-investigation response targeting a specific region or feature."""
    session_id: str
    region_label: str
    spectral_stats: dict
    answer: str
    evidence_ids: list[str]
    warnings: list[str] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    stage: int
    vlm_available: bool
    timestamp: str
