# SatQuery AI — API Documentation

## Base URL
`http://localhost:8000`

## Authentication
Stage 1: No authentication required.
Stage 3: JWT tokens via `Authorization: Bearer <token>`.

---

## Endpoints

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0-stage1",
  "stage": 1,
  "vlm_available": false,
  "timestamp": "2026-09-06T13:00:00Z"
}
```

---

### POST /api/analyze
Main analysis endpoint. Accepts multipart form data.

**Request (multipart/form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | Yes | 1 or 2 image files (GeoTIFF, TIFF, PNG, JPEG) |
| `query` | string | Yes | Natural language question |
| `mode` | string | Yes | `single_image`, `optical_sar`, or `change_analysis` |
| `date_a` | string | No | Date of first image (ISO 8601) |
| `date_b` | string | No | Date of second image (ISO 8601) |
| `sensor_a` | string | No | Sensor name for first image |
| `sensor_b` | string | No | Sensor name for second image |

**Response:**
```json
{
  "session_id": "sess_abc123",
  "task_type": "change_detection",
  "answer": "Between the two dates, significant changes were detected...",
  "measurements": [
    {
      "label": "Changed Area",
      "value": 1.42,
      "unit": "km²",
      "evidence_type": "DERIVED"
    }
  ],
  "confidence": 0.82,
  "confidence_level": "high",
  "evidence_ids": ["ev_001", "ev_002"],
  "execution_trace_id": "trace_xyz",
  "warnings": [],
  "preview_url": "/outputs/sess_abc123/preview.png",
  "overlay_url": "/outputs/sess_abc123/change_overlay.png",
  "report_urls": {
    "json": "/api/reports/sess_abc123?format=json",
    "markdown": "/api/reports/sess_abc123?format=markdown"
  }
}
```

---

### GET /api/evidence/{evidence_id}
Retrieve a specific evidence record.

**Response:**
```json
{
  "evidence_id": "ev_001",
  "task": "change_detection",
  "evidence_type": "DERIVED",
  "source_image": "image_t2.tif",
  "tool": "change_vector_otsu",
  "result": {
    "change_percentage": 12.4,
    "changed_area_km2": 1.42
  },
  "confidence": 0.82,
  "warnings": []
}
```

---

### GET /api/reports/{session_id}
Download analysis report.

**Query Parameters:**
- `format`: `json` (default) or `markdown`

---

### POST /api/query
Run a natural language query against an already-uploaded image.

**Request:**
```json
{
  "session_id": "sess_abc123",
  "query": "Has the forest area decreased?"
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "error": "RasterLoadError",
  "message": "Failed to open file: not a valid TIFF",
  "detail": "...",
  "timestamp": "..."
}
```

Common HTTP status codes:
- `400` Bad Request — invalid input
- `404` Not Found — session/evidence/report not found
- `422` Unprocessable Entity — validation error
- `500` Internal Server Error — analysis failed
