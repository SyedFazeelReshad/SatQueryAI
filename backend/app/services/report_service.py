from app.reports.markdown import generate_markdown_report
from app.reports.json_report import generate_json_report
from app.models.responses import AnalysisResult
import json
from pathlib import Path

def generate_reports(result: AnalysisResult, session_id: str) -> dict[str, Path]:
    md = generate_markdown_report(result, session_id)
    js = generate_json_report(result, session_id)
    return {"markdown": md, "json": js}
