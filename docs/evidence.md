# SatQuery AI — Evidence System

## Philosophy

Every result in SatQuery AI must be traceable to evidence.
The evidence system ensures scientific honesty and auditability.

## Evidence Types

| Type | Description | Example |
|------|-------------|---------|
| `OBSERVED` | Directly available from source imagery metadata | Image dimensions, CRS, acquisition date |
| `DERIVED` | Calculated deterministically from raster data | NDVI value, area in km², change percentage |
| `DETECTED` | Result of an algorithmic detection | Connected component, edge line |
| `AI_DETECTED` | Result of an AI model with confidence score | VQA answer, captioned region |
| `INFERRED` | Hypothesis derived from evidence | "This appears to be..." |
| `SYNTHETIC` | Artificial demonstration data | Sample/demo results |

**Critical Rule:** INFERRED must never be presented as OBSERVED or DERIVED.

## Evidence Record Schema

```json
{
  "evidence_id": "ev_001",
  "task": "change_detection",
  "evidence_type": "DERIVED",
  "source_image": "image_2025.tif",
  "source_date": "2025-01-15",
  "sensor": "Sentinel-2",
  "tool": "change_vector_otsu",
  "model": null,
  "parameters": {
    "threshold_method": "otsu",
    "min_area_pixels": 5
  },
  "result": {
    "change_percentage": 12.4,
    "changed_pixels": 4960,
    "changed_area_km2": 1.42,
    "threshold_value": 0.187
  },
  "confidence": 0.82,
  "confidence_basis": "Otsu stability + valid pixel fraction 0.97",
  "geometry": null,
  "timestamp": "2026-09-06T13:00:00Z",
  "warnings": []
}
```

## Confidence Estimation

Confidence is estimated from real signals, not fabricated:

- **Band availability**: Can required spectral bands be read?
- **Valid pixel fraction**: What proportion of pixels have valid (non-nodata) values?
- **Registration quality**: How well-aligned are bi-temporal images?
- **Change magnitude stability**: How stable is the Otsu threshold?
- **Input resolution**: Is the GSD appropriate for the analysis?

If confidence cannot be reliably estimated, return `null` with level `"unavailable"`.
