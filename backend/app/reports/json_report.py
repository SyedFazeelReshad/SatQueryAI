import json
from app.models.responses import AnalysisResult
from pathlib import Path
from app.core.config import settings

def generate_json_report(result: AnalysisResult, session_id: str) -> Path:
    report_path = settings.output_dir / f"report_{session_id}.json"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
        
    return report_path
