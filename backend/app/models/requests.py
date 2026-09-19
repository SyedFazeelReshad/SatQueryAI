from pydantic import BaseModel
from enum import Enum

class AnalysisMode(str, Enum):
    SINGLE_IMAGE = "single_image"
    OPTICAL_SAR = "optical_sar"
    CHANGE_ANALYSIS = "change_analysis"

class AnalyzeRequest(BaseModel):
    query: str
    mode: AnalysisMode
    date_a: str | None = None
    date_b: str | None = None
    sensor_a: str | None = None
    sensor_b: str | None = None
    band_mapping: dict | None = None

class QueryRequest(BaseModel):
    session_id: str
    query: str
