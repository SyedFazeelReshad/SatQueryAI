from typing import Any
from app.evidence.schema import ConfidenceEstimate
from app.geospatial.raster import RasterMetadata

def estimate_confidence(
    tool: Any,
    result: dict | None = None,
    metadata: RasterMetadata | None = None,
    warnings: list[str] | None = None
) -> ConfidenceEstimate:
    # If called with a list of evidence IDs
    if isinstance(tool, list):
        evidence_ids = tool
        n = len(evidence_ids)
        score = min(0.95, 0.6 + 0.08 * n) if n > 0 else 0.5
        level = "high" if score > 0.8 else ("medium" if score > 0.5 else "low")
        return ConfidenceEstimate(
            score=round(score, 2),
            level=level,
            basis=f"Confidence aggregated from {n} verified evidence records.",
            signals={"n_evidence": n}
        )

    signals = {}
    base_score = 1.0
    warnings = warnings or []
    result = result or {}
    
    if metadata and metadata.warnings:
        signals["metadata_warnings"] = len(metadata.warnings)
        base_score -= 0.1 * len(metadata.warnings)
        
    if warnings:
        signals["analysis_warnings"] = len(warnings)
        base_score -= 0.2 * len(warnings)
        
    if tool == "change_detection":
        if "quality_score" in result:
            signals["registration_quality"] = result["quality_score"]
            base_score *= result["quality_score"]
            
    base_score = max(0.0, min(1.0, base_score))
    
    if base_score > 0.8:
        level = "high"
    elif base_score > 0.5:
        level = "medium"
    else:
        level = "low"
        
    return ConfidenceEstimate(
        score=base_score,
        level=level,
        basis=f"Rule-based estimation based on tool {tool}, metadata, and warnings.",
        signals=signals
    )
