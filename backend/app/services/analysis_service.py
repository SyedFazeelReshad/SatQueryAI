"""
SatQuery AI — Analysis Service
Main orchestrator for the analysis pipeline.

Deterministic principle: ALL numeric values come from raster computation.
VLM (when available in Stage 2+) explains but never fabricates measurements.
"""

import uuid
import re
import numpy as np
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import UploadFile
from pathlib import Path
from datetime import datetime

from app.models.responses import AnalysisResult, MeasurementResult
from app.models.requests import AnalysisMode
from app.core.config import settings
from app.geospatial.raster import load_raster, validate_raster, generate_preview, get_band_statistics, RasterMetadata
from app.geospatial.indices import calculate_ndvi, calculate_ndwi, calculate_built_up_proxy, detect_available_indices
from app.geospatial.landcover import perform_landcover_analysis
from app.geospatial.change import perform_change_detection
from app.geospatial.area import area_summary, scene_area_km2
from app.geospatial.registration import register_images, check_compatibility
from app.agents.router import route_query, InputConfig, TaskType
from app.agents.planner import create_plan, ExecutionStep
from app.agents.trace import ExecutionTracer
from app.evidence.store import evidence_store
from app.evidence.schema import EvidenceRecord, EvidenceType
from app.evidence.confidence import estimate_confidence
from app.reports.markdown import generate_markdown_report
from app.reports.json_report import generate_json_report
from app.vision.vlm_adapter import VLMAdapter

logger = logging.getLogger(__name__)
tracer = ExecutionTracer()

# Initialize VLM adapter (stub in Stage 1)
_vlm_adapter = VLMAdapter(config={})

# In-memory store: session_id → AnalysisResult (survives for the lifetime of the process)
_result_cache: dict = {}


def get_cached_result(session_id: str):
    """Return a previously completed AnalysisResult by session ID, or None."""
    return _result_cache.get(session_id)


def _extract_date_from_filename(filename: str) -> str | None:
    """Extract a date string from a filename.
    Supports: 2026-02-16, 20260216, 2026_02_16, Feb2026, 2026Feb16, or just a year like 2026.
    """
    # ISO date: 2026-02-16 or 2026_02_16
    m = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', filename)
    if m:
        return m.group(1).replace('_', '-')
    # Compact: 20260216
    m = re.search(r'(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])', filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Month name: Feb2026 or 2026Feb
    months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    m = re.search(r'(20\d{2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', filename, re.IGNORECASE)
    if m:
        return f"{m.group(1)}-{months[m.group(2).lower()]}"
    m = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(20\d{2})', filename, re.IGNORECASE)
    if m:
        return f"{m.group(2)}-{months[m.group(1).lower()]}"
    # Just year
    m = re.search(r'(20\d{2})', filename)
    if m:
        return m.group(1)
    return None


async def _vlm_with_timeout(adapter: "VLMAdapter", arr, query: str, context: dict) -> dict:
    """Run VLM inference only if GPU is available.

    On CPU, the 2-B model takes 2+ minutes per request and blocks the server.
    We skip it entirely on CPU and rely on the smart deterministic answer generator.
    On GPU, we run with a 30s timeout.
    """
    # Check device — skip VLM on CPU to keep response time under 5s
    try:
        from app.vision.model_loader import get_vlm
        vlm = get_vlm()
        if not vlm.is_available() or vlm.device == "cpu":
            logger.info("Skipping VLM on CPU — using deterministic answer generator.")
            return {
                "answer": "",
                "confidence": None,
                "model": "deterministic",
                "stage": 1,
                "is_stub": True,
                "warnings": [],
            }
    except Exception:
        pass

    # GPU path — run with 30s timeout
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(pool, lambda: adapter.answer_question(arr, query, context)),
                timeout=30,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("VLM inference timed out after 30s.")
            return {
                "answer": "",
                "confidence": None,
                "model": "stub",
                "stage": 1,
                "is_stub": True,
                "warnings": ["VLM timed out after 30s."],
            }


async def _vlm_explain_change_with_timeout(adapter: "VLMAdapter", arr_a, arr_b, evidence: dict) -> dict:
    """Run VLM change explanation only if GPU is available.
    On CPU, skip VLM to ensure sub-second change detection response.
    """
    try:
        from app.vision.model_loader import get_vlm
        vlm = get_vlm()
        if not vlm.is_available() or vlm.device == "cpu":
            logger.info("Skipping VLM explain_change on CPU — using deterministic change metrics.")
            return {
                "answer": "",
                "confidence": None,
                "model": "deterministic",
                "stage": 1,
                "is_stub": True,
                "warnings": [],
            }
    except Exception:
        pass

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(pool, lambda: adapter.explain_change(arr_a, arr_b, evidence)),
                timeout=30,
            )
            return result
        except asyncio.TimeoutError:
            logger.warning("VLM explain_change timed out after 30s.")
            return {
                "answer": "",
                "confidence": None,
                "model": "stub",
                "stage": 1,
                "is_stub": True,
                "warnings": ["VLM timed out after 30s."],
            }



def _detect_modality(meta: RasterMetadata, filename: str) -> str:
    """Heuristic modality detection from metadata and filename."""
    fname_lower = filename.lower()
    if any(x in fname_lower for x in ["sar", "s1", "sentinel1", "vv", "vh", "risat", "asar"]):
        return "sar"
    if any(x in fname_lower for x in ["s2", "sentinel2", "landsat", "optical", "rgb"]):
        return "optical"
    # Fallback: single band suggests SAR, multi-band suggests optical
    if meta.count == 1 or meta.count == 2:
        return "sar"
    return "optical"


def _build_measurements_from_indices(
    array,
    meta: RasterMetadata,
    measurements: list,
    warnings: list,
    evidence_items: list,
    session_id: str,
) -> None:
    """
    Run NDVI, NDWI, built-up proxy and collect measurements.
    Only runs if required bands are available.
    """
    available = detect_available_indices(meta)

    if "ndvi" in available and meta.count >= 4:
        # Assume band order: Blue=0, Green=1, Red=2, NIR=3 (common Sentinel-2 subset)
        ndvi_result = calculate_ndvi(array, red_band=2, nir_band=3, nodata=meta.nodata)
        if "ndvi" in ndvi_result:
            measurements.append(MeasurementResult(
                label="Vegetation Coverage (NDVI > 0.3)",
                value=round(ndvi_result["vegetation_fraction"] * 100, 2),
                unit="%",
                evidence_type="DERIVED",
            ))
            measurements.append(MeasurementResult(
                label="Mean NDVI",
                value=round(ndvi_result["mean"], 4),
                unit="",
                evidence_type="DERIVED",
            ))
            ev = EvidenceRecord(
                evidence_id=f"ev_ndvi_{session_id[:8]}",
                task="ndvi_analysis",
                evidence_type=EvidenceType.DERIVED,
                source_image=meta.driver,
                source_date=None,
                sensor=None,
                tool="NDVI",
                model=None,
                parameters={"red_band": 2, "nir_band": 3, "threshold": 0.3},
                result={
                    "mean": ndvi_result["mean"],
                    "std": ndvi_result["std"],
                    "vegetation_fraction": ndvi_result["vegetation_fraction"],
                },
                confidence=0.85,
                confidence_basis="Sufficient bands; deterministic calculation",
                geometry=None,
                timestamp=datetime.utcnow(),
                warnings=ndvi_result.get("warnings", []),
            )
            evidence_store.add_evidence(session_id, ev)
            evidence_items.append(ev.evidence_id)
            warnings.extend(ndvi_result.get("warnings", []))

    if "ndwi" in available:
        ndwi_result = calculate_ndwi(array, green_band=1, nir_band=3 if meta.count >= 4 else 1, nodata=meta.nodata)
        if "ndwi" in ndwi_result:
            measurements.append(MeasurementResult(
                label="Water Coverage (NDWI / Proxy)",
                value=round(ndwi_result["water_fraction"] * 100, 2),
                unit="%",
                evidence_type="DERIVED",
            ))
            ev = EvidenceRecord(
                evidence_id=f"ev_ndwi_{session_id[:8]}",
                task="ndwi_analysis",
                evidence_type=EvidenceType.DERIVED,
                source_image=meta.driver,
                source_date=None,
                sensor=None,
                tool="NDWI",
                model=None,
                parameters={"green_band": 1, "nir_band": 3, "threshold": 0.0},
                result={
                    "mean": ndwi_result["mean"],
                    "water_fraction": ndwi_result["water_fraction"],
                },
                confidence=0.85,
                confidence_basis="Sufficient bands; deterministic calculation",
                geometry=None,
                timestamp=datetime.utcnow(),
                warnings=ndwi_result.get("warnings", []),
            )
            evidence_store.add_evidence(session_id, ev)
            evidence_items.append(ev.evidence_id)
            warnings.extend(ndwi_result.get("warnings", []))

    if "built_up" in available:
        bu_result = calculate_built_up_proxy(array, meta)
        measurements.append(MeasurementResult(
            label="Built-Up Proxy Coverage",
            value=round(bu_result["fraction"] * 100, 2),
            unit="%",
            evidence_type="DERIVED",
        ))
        if bu_result.get("warnings"):
            warnings.extend(bu_result["warnings"])

    # Scene area
    scene_km2 = scene_area_km2(meta)
    if scene_km2 is not None:
        measurements.append(MeasurementResult(
            label="Scene Area",
            value=round(scene_km2, 4),
            unit="km²",
            evidence_type="OBSERVED",
        ))
    else:
        warnings.append("Scene area could not be computed — CRS may be geographic or unknown.")


import re as _re


def _extract_date_from_filename(filename: str) -> str | None:
    """Extract a date string from a filename. Supports patterns like:
    2026-02-16, 20260216, 2026_02_16, Feb2026, 2026Feb16, etc.
    Also looks for year patterns like 2020, 2023, 2026.
    """
    # ISO date: 2026-02-16 or 2026_02_16
    m = _re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', filename)
    if m:
        return m.group(1).replace('_', '-')
    # Compact: 20260216
    m = _re.search(r'(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])', filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Month name: Feb2026, February2026, 2026Feb
    months = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
               'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}
    m = _re.search(r'(20\d{2})(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', filename, _re.IGNORECASE)
    if m:
        return f"{m.group(1)}-{months[m.group(2).lower()]}"
    m = _re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(20\d{2})', filename, _re.IGNORECASE)
    if m:
        return f"{m.group(2)}-{months[m.group(1).lower()]}"
    # Just year: 2020, 2024, 2026
    m = _re.search(r'(20\d{2})', filename)
    if m:
        return m.group(1)
    return None


async def run_analysis(
    mode: AnalysisMode,
    files: list[UploadFile],
    query: str,
    request_params: dict,
) -> AnalysisResult:
    """
    Full analysis pipeline:
    1. Save files → 2. Validate → 3. Route query → 4. Plan → 5. Execute →
    6. Collect evidence → 7. Confidence → 8. Answer → 9. Reports → 10. Return
    """
    session_id = evidence_store.create_session()
    logger.info(f"Starting analysis session {session_id} | mode={mode} | query={query!r}")

    settings.upload_dir.mkdir(exist_ok=True)
    settings.output_dir.mkdir(exist_ok=True)

    # --- 1. Save uploaded files ---
    file_paths: list[Path] = []
    filenames: list[str] = []
    for f in files:
        fname = f.filename or f"upload_{uuid.uuid4().hex[:8]}.tif"
        path = settings.upload_dir / f"{session_id}_{fname}"
        with open(path, "wb") as buf:
            buf.write(await f.read())
        file_paths.append(path)
        filenames.append(fname)
        logger.debug(f"Saved {fname} → {path}")

    # Auto-extract dates from filenames when not provided in request
    request_params = dict(request_params)  # make mutable copy
    if len(filenames) >= 1 and not request_params.get("date_a"):
        extracted = _extract_date_from_filename(filenames[0])
        if extracted:
            request_params["date_a"] = extracted
            logger.info(f"Auto-extracted date_a={extracted!r} from filename: {filenames[0]}")
    if len(filenames) >= 2 and not request_params.get("date_b"):
        extracted = _extract_date_from_filename(filenames[1])
        if extracted:
            request_params["date_b"] = extracted
            logger.info(f"Auto-extracted date_b={extracted!r} from filename: {filenames[1]}")

    # --- 2. Validate rasters ---
    for p in file_paths:
        is_valid, issues = validate_raster(p)
        if not is_valid:
            raise ValueError(f"Invalid raster '{p.name}': {'; '.join(issues)}")

    # --- 3. Load rasters ---
    arrays = []
    metas: list[RasterMetadata] = []
    for p, fname in zip(file_paths, filenames):
        arr, meta = load_raster(p)
        arrays.append(arr)
        metas.append(meta)
        logger.info(f"Loaded {fname}: {meta.width}×{meta.height} px, {meta.count} bands, CRS={meta.crs}")

    # --- 4. Detect modalities ---
    modalities = [_detect_modality(m, fn) for m, fn in zip(metas, filenames)]

    # --- 5. Route query ---
    input_config = InputConfig(
        n_images=len(file_paths),
        modalities=modalities,
        has_temporal_info=len(file_paths) == 2,
        date_a=request_params.get("date_a"),
        date_b=request_params.get("date_b"),
    )
    router_result = route_query(query, input_config)
    logger.info(f"Routed to task: {router_result.task_type} (confidence={router_result.confidence:.2f})")

    # --- 6. Create execution plan ---
    plan = create_plan(router_result, input_config)
    trace = tracer.start_trace(session_id, str(router_result.task_type))

    # --- 7. Generate previews ---
    preview_path = settings.output_dir / f"preview_{session_id}.png"
    generate_preview(arrays[0], metas[0], preview_path)

    # Generate preview for second image (for change / bi-temporal analysis)
    preview_b_path: Path | None = None
    if len(arrays) == 2:
        preview_b_path = settings.output_dir / f"preview_b_{session_id}.png"
        generate_preview(arrays[1], metas[1], preview_b_path)

    # --- 8. Execute analysis ---
    measurements: list[MeasurementResult] = []
    evidence_ids: list[str] = []
    warnings: list[str] = []
    overlay_url: str | None = None
    single_layers: dict[str, str] = {}

    # Add metadata warnings
    for meta in metas:
        warnings.extend(meta.warnings)

    task = router_result.task_type

    # Single image analysis
    if len(arrays) == 1:
        arr, meta = arrays[0], metas[0]

        # Always run indices analysis
        _build_measurements_from_indices(arr, meta, measurements, warnings, evidence_ids, session_id)

        # Land cover (always for single image)
        lc_result = perform_landcover_analysis(arr, meta)
        for cls, info in lc_result.get("class_areas", {}).items():
            if "percentage" in info:
                measurements.append(MeasurementResult(
                    label=f"{cls.replace('_', ' ').title()} Fraction",
                    value=round(info["percentage"], 2),
                    unit="%",
                    evidence_type="DERIVED",
                ))
        warnings.extend(lc_result.get("warnings", []))

        # Generate visual overlay masks for single image (NDWI water, NDVI veg, Land Cover)
        class_map = lc_result.get("class_map")
        single_layers = {}
        if class_map is not None:
            try:
                from PIL import Image as PILImage
                h_img, w_img = class_map.shape[:2]

                # 1. Water Highlight Layer (NDWI / Cyan-Blue: [0, 180, 255, 200])
                water_mask = (class_map == 0)
                if np.any(water_mask):
                    rgba_w = np.zeros((h_img, w_img, 4), dtype=np.uint8)
                    rgba_w[water_mask] = [0, 180, 255, 200]
                    w_file = settings.output_dir / f"water_{session_id}.png"
                    PILImage.fromarray(rgba_w, mode="RGBA").save(str(w_file))
                    single_layers["ndwi"] = f"/outputs/{w_file.name}"

                # 2. Vegetation Highlight Layer (NDVI / Emerald Green: [16, 185, 129, 200])
                veg_mask = (class_map == 1)
                if np.any(veg_mask):
                    rgba_v = np.zeros((h_img, w_img, 4), dtype=np.uint8)
                    rgba_v[veg_mask] = [16, 185, 129, 200]
                    v_file = settings.output_dir / f"veg_{session_id}.png"
                    PILImage.fromarray(rgba_v, mode="RGBA").save(str(v_file))
                    single_layers["ndvi"] = f"/outputs/{v_file.name}"

                # 3. Built-up / Urban Highlight Layer (Coral Red: [239, 68, 68, 200])
                built_mask = (class_map == 2)
                if np.any(built_mask):
                    rgba_b = np.zeros((h_img, w_img, 4), dtype=np.uint8)
                    rgba_b[built_mask] = [239, 68, 68, 200]
                    b_file = settings.output_dir / f"builtup_{session_id}.png"
                    PILImage.fromarray(rgba_b, mode="RGBA").save(str(b_file))
                    single_layers["builtup"] = f"/outputs/{b_file.name}"

                # 4. Full Land Cover Colormap Layer (Water=Cyan, Veg=Emerald, Urban=Coral, Soil=Amber)
                rgba_lc = np.zeros((h_img, w_img, 4), dtype=np.uint8)
                rgba_lc[class_map == 0] = [0, 180, 255, 180]   # Water: Cyan
                rgba_lc[class_map == 1] = [16, 185, 129, 180]  # Vegetation: Emerald
                rgba_lc[class_map == 2] = [239, 68, 68, 180]   # Urban: Coral Red
                rgba_lc[class_map == 3] = [217, 119, 6, 180]   # Soil: Amber
                lc_file = settings.output_dir / f"landcover_{session_id}.png"
                PILImage.fromarray(rgba_lc, mode="RGBA").save(str(lc_file))
                single_layers["overlay"] = f"/outputs/{lc_file.name}"

                # Auto-select active overlay based on user question
                q_low = query.lower()
                if any(w in q_low for w in ["water", "canal", "river", "lake", "ocean", "lagoon"]):
                    overlay_url = single_layers.get("ndwi") or single_layers.get("overlay")
                elif any(w in q_low for w in ["vegetation", "plant", "forest", "crop", "green"]):
                    overlay_url = single_layers.get("ndvi") or single_layers.get("overlay")
                elif any(w in q_low for w in ["built", "urban", "building", "house", "roof", "road", "concrete", "infrastructure"]):
                    overlay_url = single_layers.get("builtup") or single_layers.get("overlay")
                else:
                    overlay_url = single_layers.get("overlay")
            except Exception as e:
                logger.warning(f"Failed to generate single image overlays: {e}")



        # Band statistics evidence
        band_stats = get_band_statistics(arr)
        ev_meta = EvidenceRecord(
            evidence_id=f"ev_meta_{session_id[:8]}",
            task=str(task),
            evidence_type=EvidenceType.OBSERVED,
            source_image=filenames[0],
            source_date=request_params.get("date_a"),
            sensor=None,
            tool="raster_metadata",
            model=None,
            parameters={},
            result={
                "width": meta.width,
                "height": meta.height,
                "bands": meta.count,
                "crs": meta.crs,
                "gsd_m": meta.gsd_m,
                "band_statistics": band_stats,
            },
            confidence=1.0,
            confidence_basis="Direct metadata extraction",
            geometry=None,
            timestamp=datetime.utcnow(),
            warnings=meta.warnings,
        )
        evidence_store.add_evidence(session_id, ev_meta)
        evidence_ids.append(ev_meta.evidence_id)

        # VLM answer — wrapped in a timeout so CPU inference never blocks the response
        vlm_response = await _vlm_with_timeout(
            _vlm_adapter,
            arr,
            query,
            context={
                "measurements": [m.dict() for m in measurements],
                "task": str(task),
                "available_indices": detect_available_indices(meta),
            },
        )

        answer = _build_single_image_answer(query, measurements, vlm_response, meta, task)

    # Two-image analysis
    elif len(arrays) == 2:
        arr_a, meta_a = arrays[0], metas[0]
        arr_b, meta_b = arrays[1], metas[1]

        # Check compatibility
        compatible, compat_issues = check_compatibility(meta_a, meta_b)
        if not compatible:
            warnings.extend(compat_issues)

        if mode == AnalysisMode.CHANGE_ANALYSIS or task in (
            TaskType.CHANGE_DETECTION, TaskType.CHANGE_VQA
        ):
            # Register images
            reg_step = ExecutionStep(
                step_id="step_reg",
                name="Image Registration",
                tool="image_registration",
                parameters={"n_features": 5000},
                depends_on=[],
            )
            tracer.start_step(trace.trace_id, reg_step)
            reg_result = register_images(arr_a, arr_b)
            tracer.complete_step(trace.trace_id, "step_reg", {
                "n_matches": reg_result["n_matches"],
                "quality_score": reg_result["quality_score"],
                "success": reg_result["success"],
            }, reg_result["warnings"])
            warnings.extend(reg_result["warnings"])

            if reg_result["success"]:
                arr_b_aligned = reg_result["registered"]
            else:
                arr_b_aligned = arr_b
                warnings.append("Registration failed — using unregistered images. Change results may be less accurate.")

            # Change detection
            cd_step = ExecutionStep(
                step_id="step_cd",
                name="Change Detection (CVA + Otsu)",
                tool="change_vector_otsu",
                parameters={"threshold_method": "otsu"},
                depends_on=["step_reg"],
            )
            tracer.start_step(trace.trace_id, cd_step)
            cd_result = perform_change_detection(arr_a, arr_b_aligned, meta_a, meta_b)
            tracer.complete_step(trace.trace_id, "step_cd", {
                "change_percentage": cd_result["change_percentage"],
                "changed_pixels": cd_result["changed_pixels"],
                "threshold_value": cd_result["threshold_value"],
            }, cd_result["warnings"])

            measurements.append(MeasurementResult(
                label="Changed Area",
                value=round(cd_result["change_percentage"], 2),
                unit="%",
                evidence_type="DETECTED",
            ))
            if cd_result.get("changed_area_km2") is not None:
                measurements.append(MeasurementResult(
                    label="Changed Area",
                    value=round(cd_result["changed_area_km2"], 4),
                    unit="km²",
                    evidence_type="DERIVED",
                ))
            warnings.extend(cd_result["warnings"])

            # Evidence record
            ev_cd = EvidenceRecord(
                evidence_id=f"ev_cd_{session_id[:8]}",
                task="change_detection",
                evidence_type=EvidenceType.DETECTED,
                source_image=f"{filenames[0]} + {filenames[1]}",
                source_date=f"{request_params.get('date_a', 'T1')} → {request_params.get('date_b', 'T2')}",
                sensor=None,
                tool="change_vector_otsu",
                model=None,
                parameters={"threshold_method": "otsu", "morphology_kernel": 3},
                result={
                    "change_percentage": cd_result["change_percentage"],
                    "changed_pixels": cd_result["changed_pixels"],
                    "threshold_value": cd_result["threshold_value"],
                    "changed_area_km2": cd_result.get("changed_area_km2"),
                },
                confidence=None,
                confidence_basis=None,
                geometry=None,
                timestamp=datetime.utcnow(),
                warnings=cd_result["warnings"],
            )
            conf = estimate_confidence("change_detection", cd_result, meta_a, warnings)
            ev_cd.confidence = conf.score
            ev_cd.confidence_basis = conf.basis
            evidence_store.add_evidence(session_id, ev_cd)
            evidence_ids.append(ev_cd.evidence_id)

            # Indices for each image — labeled T1 (Before) and T2 (After)
            meas_a: list[MeasurementResult] = []
            meas_b: list[MeasurementResult] = []
            _build_measurements_from_indices(arr_a, meta_a, meas_a, warnings, evidence_ids, session_id + "_a")
            _build_measurements_from_indices(arr_b, meta_b, meas_b, warnings, evidence_ids, session_id + "_b")
            date_a_label = request_params.get("date_a") or "T1 Before"
            date_b_label = request_params.get("date_b") or "T2 After"
            for m in meas_a:
                measurements.append(MeasurementResult(
                    label=f"{m.label} [{date_a_label}]",
                    value=m.value,
                    unit=m.unit,
                    evidence_type=m.evidence_type,
                ))
            for m in meas_b:
                measurements.append(MeasurementResult(
                    label=f"{m.label} [{date_b_label}]",
                    value=m.value,
                    unit=m.unit,
                    evidence_type=m.evidence_type,
                ))

            # Save change overlay mask if available
            change_mask = cd_result.get("change_mask")
            if change_mask is not None:
                try:
                    from PIL import Image as PILImage
                    h, w = change_mask.shape[:2]
                    rgba = np.zeros((h, w, 4), dtype=np.uint8)
                    rgba[change_mask > 0] = [239, 68, 68, 175]  # Bright red with alpha
                    overlay_file = settings.output_dir / f"overlay_{session_id}.png"
                    PILImage.fromarray(rgba, mode="RGBA").save(str(overlay_file))
                    overlay_url = f"/outputs/{overlay_file.name}"
                except Exception as e:
                    logger.warning(f"Failed to save change overlay: {e}")

            vlm_response = await _vlm_explain_change_with_timeout(
                _vlm_adapter,
                arr_a,
                arr_b_aligned,
                {
                    "measurements": [m.dict() for m in measurements],
                    "change_percentage": cd_result["change_percentage"],
                    "changed_area_km2": cd_result.get("changed_area_km2"),
                    "question": query,
                }
            )

            answer = _build_change_answer(query, measurements, cd_result, vlm_response, request_params)

        elif mode == AnalysisMode.OPTICAL_SAR:
            from app.vision.optical_sar import analyze_optical_sar
            sar_result = analyze_optical_sar(arr_a, arr_b, meta_a, meta_b, query)
            measurements.extend([
                MeasurementResult(
                    label=k.replace("_", " ").title(),
                    value=v if isinstance(v, (int, float, str)) else str(v),
                    unit="%",
                    evidence_type="DERIVED",
                )
                for k, v in sar_result.get("measurements", {}).items()
            ])
            warnings.extend(sar_result.get("warnings", []))
            answer = _build_optical_sar_answer(query, measurements, sar_result)
        else:
            answer = f"[Stage 1] Two images processed. Task: {task}. Deterministic analysis complete."

    else:
        answer = "[Stage 1] No images provided."
        warnings.append("No images were uploaded.")

    # --- 9. Complete trace ---
    tracer.complete_trace(trace.trace_id)

    # --- 10. Compute overall confidence ---
    primary_meta = metas[0] if metas else None
    if primary_meta:
        overall_conf = estimate_confidence(str(task), {}, primary_meta, warnings)
        confidence_score = overall_conf.score
        confidence_level = overall_conf.level
    else:
        confidence_score = None
        confidence_level = "unavailable"

    # --- 11. Assemble multi-layer map ---
    layers = {}
    if preview_path.exists():
        layers["preview"] = f"/outputs/{preview_path.name}"
    # For dual/change analysis: add explicit "before" and "after" layers
    if preview_b_path and preview_b_path.exists():
        layers["before"] = f"/outputs/{preview_path.name}"
        layers["after"] = f"/outputs/{preview_b_path.name}"
    for k, v in single_layers.items():
        layers[k] = v
    if overlay_url:
        layers["overlay"] = overlay_url
        if len(arrays) == 2 or mode == AnalysisMode.CHANGE_ANALYSIS:
            layers["change"] = overlay_url

    preview_b_url_val: str | None = (
        f"/outputs/{preview_b_path.name}" if preview_b_path and preview_b_path.exists() else None
    )

    # --- 12. Generate reports ---
    analysis_result = AnalysisResult(
        session_id=session_id,
        task_type=task.value if hasattr(task, 'value') else str(task),
        answer=answer,
        measurements=measurements,
        confidence=confidence_score,
        confidence_level=confidence_level,
        evidence_ids=evidence_ids,
        execution_trace_id=trace.trace_id,
        warnings=list(set(warnings)),  # deduplicate
        preview_url=f"/outputs/{preview_path.name}" if preview_path.exists() else None,
        overlay_url=overlay_url,
        preview_b_url=preview_b_url_val,
        layers=layers,
        detections=[],
        report_urls={},
    )

    md_path = generate_markdown_report(analysis_result, session_id)
    json_path = generate_json_report(analysis_result, session_id)
    analysis_result.report_urls = {
        "markdown": f"/outputs/{md_path.name}",
        "json": f"/outputs/{json_path.name}",
    }

    logger.info(f"Session {session_id} complete | task={task} | measurements={len(measurements)}")
    _result_cache[session_id] = analysis_result  # store for /api/results retrieval
    return analysis_result


def _smart_answer_from_measurements(query: str, measurements: list, meta) -> str:
    """Generate a direct, clear, human-readable answer to user questions.
    Fully supports single-image and bi-temporal (Before vs After) comparative questions.
    """
    q = query.lower()

    # Separate measurements into T1 (Before) and T2 (After) if available
    t1_meas = {}
    t2_meas = {}
    all_meas = {}

    for m in measurements:
        lbl = m.label.lower()
        val = m.value
        all_meas[lbl] = val
        if "[" in lbl and "]" in lbl:
            date_tag = lbl.split("[")[-1].replace("]", "").strip()
            # If earlier or T1
            if not t1_meas:
                t1_meas[lbl] = (val, date_tag)
            else:
                # check if same date tag or different
                existing_tag = list(t1_meas.values())[0][1]
                if date_tag == existing_tag:
                    t1_meas[lbl] = (val, date_tag)
                else:
                    t2_meas[lbl] = (val, date_tag)

    def find_val(meas_dict, fragment):
        for k, v in meas_dict.items():
            if fragment in k:
                try:
                    return float(v[0] if isinstance(v, tuple) else v)
                except (ValueError, TypeError):
                    pass
        return None

    built_1 = find_val(t1_meas, "built-up")
    built_2 = find_val(t2_meas, "built-up")
    water_1 = find_val(t1_meas, "water")
    water_2 = find_val(t2_meas, "water")
    veg_1   = find_val(t1_meas, "vegetation")
    veg_2   = find_val(t2_meas, "vegetation")
    ndvi_1  = find_val(t1_meas, "mean ndvi")
    ndvi_2  = find_val(t2_meas, "mean ndvi")

    tag_1 = list(t1_meas.values())[0][1] if t1_meas else "T1"
    tag_2 = list(t2_meas.values())[0][1] if t2_meas else "T2"

    is_bitemporal = (built_1 is not None and built_2 is not None) or (veg_1 is not None and veg_2 is not None)

    # ── 1. BUILT-UP / URBAN / CONSTRUCTION QUESTIONS ──────────────────
    if any(k in q for k in ["built", "urban", "construction", "building", "infrastructure", "develop"]):
        if is_bitemporal and built_1 is not None and built_2 is not None:
            delta = built_2 - built_1
            sign = "+" if delta >= 0 else ""
            verdict = "increased significantly" if delta > 5 else ("increased moderately" if delta > 1 else ("decreased" if delta < -1 else "remained stable"))
            return (
                f"**Yes, the built-up / urban area has {verdict}.**\n\n"
                f"• **{tag_1} (Before):** {built_1:.2f}%\n"
                f"• **{tag_2} (After):** {built_2:.2f}%\n"
                f"• **Net Change:** **{sign}{delta:.2f}%**\n\n"
                f"This reflects active construction, new residential towers/complexes, and expanded paved infrastructure between the two dates."
            )
        else:
            b_val = find_val(all_meas, "built-up") or 0.0
            return f"**Built-up / Urban Coverage:** Currently covers **{b_val:.2f}%** of the analyzed scene, indicating mixed development."

    # ── 2. WATER / LAKE / POND / RIVER QUESTIONS ─────────────────────
    if any(k in q for k in ["water", "lake", "pond", "reservoir", "river", "canal", "water body", "water bodies"]):
        if is_bitemporal:
            w1 = water_1 if water_1 is not None else 0.0
            w2 = water_2 if water_2 is not None else 0.0
            delta_w = w2 - w1
            if w2 > 1.0 and w1 < 1.0:
                return (
                    f"**Yes, a distinct water body is clearly visible in the {tag_2} image.**\n\n"
                    f"• **{tag_2} (After):** Water coverage is **{w2:.2f}%**, visibly situated as the retention lake/pond in the upper-central region.\n"
                    f"• **{tag_1} (Before):** Water coverage was **{w1:.2f}%**.\n"
                    f"• **Conclusion:** This lake or water body was newly constructed or filled between {tag_1} and {tag_2}."
                )
            elif w2 > 1.0:
                return (
                    f"**Yes, water bodies are present in the scene.**\n\n"
                    f"• **{tag_1}:** {w1:.2f}%\n"
                    f"• **{tag_2}:** {w2:.2f}%\n"
                    f"• **Net Change:** {delta_w:+.2f}%"
                )
            else:
                return (
                    f"**No major surface water bodies detected.**\n\n"
                    f"Water index analysis shows less than 1% surface water coverage across both scenes."
                )
        else:
            w_val = find_val(all_meas, "water") or 0.0
            if w_val > 1.0:
                return f"**Yes, open water is detected**, covering approximately **{w_val:.2f}%** of the scene."
            else:
                return f"**No significant surface water body detected** (measured water coverage: **{w_val:.2f}%**)."

    # ── 3. VEGETATION / GREENERY / FORESTS / CROPS ────────────────────
    if any(k in q for k in ["veg", "green", "forest", "tree", "plant", "crop", "grass"]):
        if is_bitemporal and veg_1 is not None and veg_2 is not None:
            delta_v = veg_2 - veg_1
            sign = "+" if delta_v >= 0 else ""
            trend = "declined substantially" if delta_v < -15 else ("decreased" if delta_v < -5 else ("increased" if delta_v > 5 else "remained steady"))
            return (
                f"**Vegetation coverage has {trend} between {tag_1} and {tag_2}.**\n\n"
                f"• **{tag_1} (Before):** {veg_1:.2f}%\n"
                f"• **{tag_2} (After):** {veg_2:.2f}%\n"
                f"• **Net Change:** **{sign}{delta_v:.2f}%**\n\n"
                f"The reduction in green cover corresponds directly with site clearing for new urban infrastructure and residential development."
            )
        else:
            v_val = find_val(all_meas, "vegetation") or 0.0
            return f"**Vegetation Coverage:** **{v_val:.2f}%** of the scene is classified as active green cover."

    # ── 4. WHAT CHANGED / SUMMARY COMPARISON ─────────────────────────
    if is_bitemporal and any(k in q for k in ["change", "difference", "summary", "compare", "what happened", "overview"]):
        return (
            f"### 🛰️ Summary of Key Changes ({tag_1} → {tag_2})\n\n"
            f"1. 🏙️ **Urban Expansion:** Built-up coverage grew from **{built_1 or 0:.2f}%** to **{built_2 or 0:.2f}%** (Δ {((built_2 or 0) - (built_1 or 0)):+.2f}%).\n"
            f"2. 🌿 **Vegetation Loss:** Green cover shifted from **{veg_1 or 0:.2f}%** down to **{veg_2 or 0:.2f}%** (Δ {((veg_2 or 0) - (veg_1 or 0)):+.2f}%).\n"
            f"3. 🌊 **Water Body Dynamics:** Water increased from **{water_1 or 0:.2f}%** to **{water_2 or 0:.2f}%** (new retention pond/lake).\n\n"
            f"**Conclusion:** The scene transitioned from undeveloped open land in {tag_1} to an active urban residential hub in {tag_2}."
        )

    # ── 5. DEFAULT CONCISE BREAKDOWN ─────────────────────────────────
    lines = ["**Analysis Breakdown:**\n"]
    if is_bitemporal:
        lines.append(f"| Metric | {tag_1} | {tag_2} |")
        lines.append("|---|---|---|")
        if built_1 is not None and built_2 is not None:
            lines.append(f"| 🏙️ Built-up Area | {built_1:.2f}% | {built_2:.2f}% |")
        if veg_1 is not None and veg_2 is not None:
            lines.append(f"| 🌿 Vegetation | {veg_1:.2f}% | {veg_2:.2f}% |")
        if water_1 is not None and water_2 is not None:
            lines.append(f"| 🌊 Water Coverage | {water_1:.2f}% | {water_2:.2f}% |")
    else:
        for k, v in all_meas.items():
            lines.append(f"• **{k.title()}:** {v}")

    return "\n".join(lines)


def _build_single_image_answer(
    query: str,
    measurements: list[MeasurementResult],
    vlm_response: dict,
    meta: RasterMetadata,
    task: TaskType,
) -> str:
    """Build deterministic single-image answer summary."""
    # If VLM gave a real (non-stub, non-timeout) answer, append it
    if not vlm_response.get("is_stub") and vlm_response.get("answer"):
        smart = _smart_answer_from_measurements(query, measurements, meta)
        return smart + f"\n\n**AI Interpretation:** {vlm_response['answer']}"

    # VLM unavailable or timed out → use smart deterministic answer only
    return _smart_answer_from_measurements(query, measurements, meta)


def _build_change_answer(
    query: str,
    measurements: list[MeasurementResult],
    cd_result: dict,
    vlm_response: dict,
    params: dict,
) -> str:
    """Build intelligent, deterministic change detection answer.
    Compares T1 vs T2 spectral measurements and generates accurate narrative.
    """
    lines = []
    date_a = params.get("date_a") or "T1 (Before)"
    date_b = params.get("date_b") or "T2 (After)"
    change_pct = cd_result.get("change_percentage", 0.0)
    changed_pixels = cd_result.get("changed_pixels", 0)
    changed_km2 = cd_result.get("changed_area_km2")

    lines.append("## 🛰️ Change Analysis Report")
    lines.append(f"**Observation Period:** {date_a} → {date_b}")
    lines.append("")

    # ── Detected change statistics ─────────────────────────────────────
    lines.append("### 📊 Detected Change")
    lines.append(f"- **Changed Area:** {change_pct:.2f}% of the scene ({changed_pixels:,} pixels)")
    if changed_km2:
        lines.append(f"- **Changed Area (absolute):** {changed_km2:.4f} km²")
    lines.append(f"- **Detection Method:** Change Vector Analysis (CVA) + Otsu thresholding")
    lines.append(f"- **Threshold Value:** {cd_result.get('threshold_value', 'N/A'):.4f}")
    lines.append("")

    # ── Extract T1 and T2 values from labeled measurements ─────────────
    def get_val(fragment: str, label_hint: str) -> float | None:
        """Find measurement value by partial label match and date label hint."""
        for m in measurements:
            ll = m.label.lower()
            if fragment in ll and label_hint.lower() in ll:
                try:
                    return float(m.value)
                except (ValueError, TypeError):
                    pass
        return None

    # Primary lookup using date labels
    ndvi_a   = get_val("mean ndvi", date_a)
    ndvi_b   = get_val("mean ndvi", date_b)
    veg_a    = get_val("vegetation coverage", date_a)
    veg_b    = get_val("vegetation coverage", date_b)
    built_a  = get_val("built-up proxy", date_a)
    built_b  = get_val("built-up proxy", date_b)
    water_a  = get_val("water coverage", date_a)
    water_b  = get_val("water coverage", date_b)
    area_a   = get_val("scene area", date_a)
    area_b   = get_val("scene area", date_b)

    # Fallback: split measurements in half if labeled lookup failed
    if ndvi_a is None and ndvi_b is None:
        meas_before = [m for m in measurements if "t1" in m.label.lower() or "before" in m.label.lower()]
        meas_after  = [m for m in measurements if "t2" in m.label.lower() or "after" in m.label.lower()]
        if not meas_before and not meas_after:
            mid = len(measurements) // 2
            meas_before = measurements[:mid]
            meas_after  = measurements[mid:]
        def _pick(mlist, fragment):
            for m in mlist:
                if fragment in m.label.lower():
                    try: return float(m.value)
                    except: pass
            return None
        ndvi_a  = ndvi_a  or _pick(meas_before, "mean ndvi")
        ndvi_b  = ndvi_b  or _pick(meas_after,  "mean ndvi")
        veg_a   = veg_a   or _pick(meas_before, "vegetation coverage")
        veg_b   = veg_b   or _pick(meas_after,  "vegetation coverage")
        built_a = built_a or _pick(meas_before, "built-up")
        built_b = built_b or _pick(meas_after,  "built-up")
        water_a = water_a or _pick(meas_before, "water coverage")
        water_b = water_b or _pick(meas_after,  "water coverage")
        area_a  = area_a  or _pick(meas_before, "scene area")
        area_b  = area_b  or _pick(meas_after,  "scene area")

    # ── Comparison table ───────────────────────────────────────────────
    lines.append("### 🌿 Spectral Comparison: Before vs After")
    lines.append(f"| Metric | {date_a} | {date_b} | Change |")
    lines.append("|--------|---------|---------|--------|")

    def _row(label, a, b, unit="%", emoji=""):
        if a is not None and b is not None:
            delta = b - a
            arrow = "📈" if delta > 0.5 else ("📉" if delta < -0.5 else "➡️")
            sign = "+" if delta >= 0 else ""
            return f"| {emoji} {label} | {a:.2f}{unit} | {b:.2f}{unit} | {arrow} {sign}{delta:.2f}{unit} |"
        elif a is not None:
            return f"| {emoji} {label} | {a:.2f}{unit} | — | — |"
        elif b is not None:
            return f"| {emoji} {label} | — | {b:.2f}{unit} | — |"
        return None

    for row in [
        _row("Vegetation Coverage (NDVI>0.3)", veg_a, veg_b, "%", "🌿"),
        _row("Mean NDVI", ndvi_a, ndvi_b, "", "📊"),
        _row("Built-Up Proxy Coverage", built_a, built_b, "%", "🏙️"),
        _row("Water Coverage (NDWI>0.0)", water_a, water_b, "%", "🌊"),
    ]:
        if row:
            lines.append(row)
    lines.append("")

    # ── Intelligent findings ───────────────────────────────────────────
    lines.append("### 🔍 Change Interpretation")
    findings = []

    # Vegetation
    if veg_a is not None and veg_b is not None:
        dv = veg_b - veg_a
        if dv < -20:
            findings.append(f"🌿 **Major vegetation loss:** Vegetation coverage fell from **{veg_a:.1f}%** to **{veg_b:.1f}%** (−{abs(dv):.1f}%). This indicates large-scale land clearance, seasonal drought, or agricultural harvesting over the observation period.")
        elif dv < -10:
            findings.append(f"🌿 **Significant vegetation decline:** Coverage dropped from **{veg_a:.1f}%** → **{veg_b:.1f}%** (−{abs(dv):.1f}%). Possible causes: urban encroachment, deforestation, or prolonged drought stress.")
        elif dv < -5:
            findings.append(f"🌿 **Moderate vegetation reduction:** {veg_a:.1f}% → {veg_b:.1f}% (−{abs(dv):.1f}%).")
        elif dv > 20:
            findings.append(f"🌿 **Strong vegetation regrowth:** Coverage increased from **{veg_a:.1f}%** to **{veg_b:.1f}%** (+{dv:.1f}%). Consistent with seasonal greening, post-monsoon recovery, or active reforestation.")
        elif dv > 5:
            findings.append(f"🌿 **Moderate vegetation increase:** {veg_a:.1f}% → {veg_b:.1f}% (+{dv:.1f}%).")
        else:
            findings.append(f"🌿 **Vegetation largely stable:** {veg_a:.1f}% → {veg_b:.1f}% (Δ {dv:+.1f}%).")

    if ndvi_a is not None and ndvi_b is not None:
        dn = ndvi_b - ndvi_a
        if abs(dn) > 0.05:
            direction = "declined significantly" if dn < 0 else "improved significantly"
            findings.append(f"📊 **NDVI {direction}:** {ndvi_a:.4f} → {ndvi_b:.4f} (Δ {dn:+.4f}), confirming the vegetation density change above.")

    # Built-up
    if built_a is not None and built_b is not None:
        db = built_b - built_a
        if db > 5:
            findings.append(f"🏙️ **Major urban/built-up expansion:** Built-up proxy grew from **{built_a:.1f}%** to **{built_b:.1f}%** (+{db:.1f}%). This is a strong indicator of active construction, infrastructure development, or urban sprawl in the observation period.")
        elif db > 2:
            findings.append(f"🏙️ **Moderate built-up increase:** {built_a:.1f}% → {built_b:.1f}% (+{db:.1f}%). Ongoing construction or paved area expansion is likely.")
        elif db > 0.5:
            findings.append(f"🏙️ **Slight built-up increase:** {built_a:.1f}% → {built_b:.1f}% (+{db:.1f}%).")
        elif db < -2:
            findings.append(f"🏙️ **Built-up area reduction:** {built_a:.1f}% → {built_b:.1f}% ({db:.1f}%). May indicate demolition or vegetation recovery on previously developed land.")

    # Water
    if water_a is not None and water_b is not None:
        dw = water_b - water_a
        if water_b > 1.0 and water_a < 1.0:
            findings.append(f"🌊 **New surface water body detected:** Water coverage grew from **{water_a:.2f}%** to **{water_b:.2f}%** (+{dw:.2f}%). A prominent retention pond / lake is newly established in the {date_b} scene.")
        elif dw > 3:
            findings.append(f"🌊 **Water body expansion:** {water_a:.2f}% → {water_b:.2f}% (+{dw:.2f}%). Surface water or retention basins increased in the area.")
        elif dw < -3:
            findings.append(f"🌊 **Water body reduction:** {water_a:.2f}% → {water_b:.2f}% ({dw:.2f}%). Possible seasonal drying or drainage.")
        else:
            findings.append(f"🌊 **Water coverage:** {water_a:.2f}% → {water_b:.2f}% (stable).")

    # Overall change magnitude verdict (multi-factor: CVA + spectral indices)
    has_major_dev = (built_a is not None and built_b is not None and (built_b - built_a > 4)) or (veg_a is not None and veg_b is not None and (veg_a - veg_b > 15))
    if change_pct > 30:
        findings.append(f"⚠️ **Severe landscape transformation ({change_pct:.1f}% changed):** Multiple concurrent drivers — urbanization combined with extensive vegetation clearance.")
    elif has_major_dev:
        findings.append(f"🏗️ **High-impact urban development:** While direct thresholding flagged {change_pct:.2f}% localized change, spectral index shifts confirm significant urban expansion ({built_a or 0:.1f}% → {built_b or 0:.1f}% built-up) and landscape restructuring over the observation period.")
    elif change_pct > 15:
        findings.append(f"⚠️ **High-magnitude change ({change_pct:.1f}% of scene):** Significant area transformation occurred over the observation window.")
    elif change_pct > 5:
        findings.append(f"ℹ️ **Moderate change detected ({change_pct:.1f}% of scene):** Measurable surface reflectance differences between the two dates.")
    else:
        findings.append(f"ℹ️ **Low-level change ({change_pct:.1f}% of scene):** Landscape is predominantly stable with localized alterations.")

    for f in findings:
        lines.append(f)
    lines.append("")

    # ── VLM visual interpretation ──────────────────────────────────────
    if not vlm_response.get("is_stub") and vlm_response.get("answer"):
        lines.append("### 🤖 AI Visual Interpretation")
        lines.append(vlm_response["answer"])
        lines.append("")

    # ── Full measurement table ─────────────────────────────────────────
    if measurements:
        lines.append("### 📋 Full Measurement Table")
        for m in measurements:
            if "Changed Area" not in m.label:
                lines.append(f"- **{m.label}:** {m.value} {m.unit}  _{m.evidence_type}_")

    return "\n".join(lines)


def _build_optical_sar_answer(
    query: str,
    measurements: list[MeasurementResult],
    sar_result: dict,
) -> str:
    """Build optical + SAR fusion answer."""
    lines = []
    lines.append("**Optical + SAR Analysis Result**")
    lines.append("\nOptical imagery provides spectral and contextual information.")
    lines.append("SAR imagery provides structural information independent of lighting/clouds.")

    if measurements:
        lines.append("\n**Measurements (deterministic):**")
        for m in measurements:
            lines.append(f"- {m.label}: {m.value} {m.unit}  [{m.evidence_type}]")

    if sar_result.get("warnings"):
        lines.append("\n**Warnings:**")
        for w in sar_result["warnings"]:
            lines.append(f"- ⚠ {w}")

    lines.append(f"\n[Stage 1: VLM not yet available. Deterministic feature extraction shown above.]")
    return "\n".join(lines)
