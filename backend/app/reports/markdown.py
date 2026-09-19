from app.models.responses import AnalysisResult
from pathlib import Path
from app.core.config import settings

def generate_markdown_report(result: AnalysisResult, session_id: str) -> Path:
    report_path = settings.output_dir / f"report_{session_id}.md"
    
    lines = [
        f"# SatQuery Analysis Report: {session_id}",
        f"\n**Task Type:** {result.task_type}",
        f"**Confidence:** {result.confidence_level} ({result.confidence})",
        "\n## Answer",
        result.answer,
        "\n## Measurements"
    ]
    
    for m in result.measurements:
        lines.append(f"- **{m.label}:** {m.value} {m.unit} ({m.evidence_type})")
        
    if result.warnings:
        lines.append("\n## Warnings")
        for w in result.warnings:
            lines.append(f"- {w}")
            
    if result.preview_url:
        lines.append(f"\n## Preview")
        lines.append(f"![Preview]({result.preview_url})")
        
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return report_path
