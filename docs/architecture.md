# SatQuery AI — Architecture Documentation

## Overview

SatQuery AI is an agentic vision-language assistant for multimodal remote-sensing image analysis. It enables non-expert users to query satellite imagery in natural language.

## System Architecture

```
┌─────────────────────────────────────────────┐
│                  USER                        │
│        Natural Language + Image Upload       │
└──────────────────┬──────────────────────────┘
                   │ HTTPS
┌──────────────────▼──────────────────────────┐
│              FRONTEND (Next.js)              │
│  Landing Page → Analyze → Results           │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│             FASTAPI BACKEND                  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │         AGENTIC LAYER                 │  │
│  │  Router → Planner → Registry         │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼──────────────────┐       │
│  │      EXECUTION ENGINE           │       │
│  │                                 │       │
│  │  ┌──────────┐  ┌─────────────┐ │       │
│  │  │ GEO      │  │  VISION     │ │       │
│  │  │ TOOLS    │  │  TOOLS      │ │       │
│  │  │          │  │             │ │       │
│  │  │ raster   │  │ vlm_adapter │ │       │
│  │  │ indices  │  │ vqa         │ │       │
│  │  │ landcover│  │ caption     │ │       │
│  │  │ change   │  │ grounding   │ │       │
│  │  │ area     │  │ optical_sar │ │       │
│  │  └──────────┘  └─────────────┘ │       │
│  └──────────────────────────────────┘      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │       EVIDENCE ENGINE                 │  │
│  │  schema → store → confidence         │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │       REPORT ENGINE                   │  │
│  │  JSON / Markdown / GeoJSON           │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Deterministic Measurements
All numeric values (area, NDVI, change percentage) are computed from raster math.
The VLM explains but never fabricates measurements.

### 2. Evidence Typing
Every piece of information is labeled:
- OBSERVED: from image metadata
- DERIVED: calculated from raster data
- DETECTED: from algorithmic detection
- AI-DETECTED: from AI model with score
- INFERRED: hypothesis from evidence
- SYNTHETIC: demo/test data

### 3. VLM Abstraction
The `vlm_adapter.py` isolates all model-specific code.
The rest of the application calls `adapter.answer_question(image, question, context)`.
This enables seamless Stage 2 → Stage 3 upgrades.

### 4. Tool Registry
Tools are defined in `configs/tools.yaml`.
The registry enables tool discovery, validation, and replacement without code changes.

### 5. Staged Development
Stage 1: Classical algorithms + stubs
Stage 2: LoRA-adapted VLM
Stage 3: Grounding DINO + SAM2 + full integration

## Data Flow

```
POST /api/analyze (multipart: images + query + mode)
        │
        ▼
[1] Save uploaded files → uploads/{session_id}/
        │
        ▼
[2] Validate rasters → RasterMetadata
        │
        ▼
[3] Route query → TaskType + InputConfig
        │
        ▼
[4] Create execution plan → ExecutionPlan
        │
        ▼
[5] Execute steps with tracer:
    a. Indices (NDVI, NDWI)
    b. Land cover classification
    c. Registration (if 2 images)
    d. Change detection (if bi-temporal)
    e. Optical-SAR fusion (if optical+SAR)
    f. VQA / Caption (via VLM adapter)
        │
        ▼
[6] Collect evidence → EvidenceStore
        │
        ▼
[7] Estimate confidence → ConfidenceEstimate
        │
        ▼
[8] Generate overlay images → outputs/{session_id}/
        │
        ▼
[9] Generate reports → outputs/{session_id}/
        │
        ▼
[10] Return AnalysisResult → frontend
```
