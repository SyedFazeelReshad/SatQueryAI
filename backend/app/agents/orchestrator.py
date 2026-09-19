"""
SatQuery AI — Full Agentic Orchestrator (Stage 3)

Autonomously decomposes natural language satellite analysis queries
into a dynamic multi-step execution graph, orchestrates geospatial
and VLM tools, handles self-correction on sensor anomalies,
and produces multi-layer analysis results with complete evidence chains.

Architecture:
    Query → Router → Planner → Orchestrator → Tools → Evidence → Report
"""

import logging
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np

from app.agents.router import RouterResult, TaskType
from app.agents.planner import ExecutionPlan
from app.agents.trace import ExecutionTracer, TraceStatus
from app.evidence.store import evidence_store
from app.evidence.schema import EvidenceRecord, EvidenceType
from app.evidence.confidence import estimate_confidence
from app.geospatial.raster import RasterMetadata
from app.geospatial.indices import (
    calculate_ndvi, calculate_ndwi, calculate_built_up_proxy,
    detect_available_indices
)
from app.geospatial.landcover import perform_landcover_analysis
from app.geospatial.change import perform_change_detection
from app.geospatial.area import area_summary, scene_area_km2
from app.geospatial.registration import register_images, check_compatibility
from app.vision.vlm_adapter import VLMAdapter
from app.vision.grounding import run_grounding

logger = logging.getLogger(__name__)


class OrchestratorResult:
    """Structured output from a full agentic orchestration run."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.answer: str = ""
        self.measurements: list[dict] = []
        self.evidence_ids: list[str] = []
        self.warnings: list[str] = []
        self.layers: dict[str, str] = {}          # layer_name → URL
        self.detections: list[dict] = []           # [{label, box, score, polygon?}]
        self.trace_id: str = ""
        self.confidence: float | None = None
        self.confidence_level: str = "low"
        self.report_urls: dict[str, str] = {}


class AgentOrchestrator:
    """
    Full multi-step agentic execution engine for SatQuery AI.

    Responsibilities:
    - Execute tools from ExecutionPlan in dependency-resolved order
    - Self-correct when sensor bands are missing or corrupted
    - Collect multi-layer raster outputs (NDVI, change mask, etc.)
    - Aggregate evidence records
    - Interface with Qwen2-VL for language answers
    - Return a fully populated OrchestratorResult
    """

    def __init__(self, output_dir: Path, config: dict = {}):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tracer = ExecutionTracer()
        self.vlm = VLMAdapter(config)

    # ─────────────────────────────────────────────────────────────────
    # PUBLIC ENTRYPOINT
    # ─────────────────────────────────────────────────────────────────

    def run(
        self,
        plan: ExecutionPlan,
        router_result: RouterResult,
        session_id: str,
        query: str,
        image_a: np.ndarray | None,
        image_b: np.ndarray | None,
        meta_a: RasterMetadata | None,
        meta_b: RasterMetadata | None,
        modality: str = "optical",
        filename_a: str = "",
        filename_b: str = "",
    ) -> OrchestratorResult:
        """Execute a full analysis plan and return OrchestratorResult."""
        result = OrchestratorResult(session_id)
        trace = self.tracer.start_trace(session_id, router_result.task_type.value)
        result.trace_id = trace.trace_id

        # Shared context passed between steps
        ctx: dict[str, Any] = {
            "image_a": image_a,
            "image_b": image_b,
            "meta_a": meta_a,
            "meta_b": meta_b,
            "modality": modality,
            "query": query,
            "session_id": session_id,
            "measurements": [],
            "warnings": [],
            "change_evidence": {},
            "ndvi_stats": None,
            "ndwi_stats": None,
            "landcover": None,
            "detections": [],
            "layers": {},
        }

        # Execute plan steps in order
        completed: set[str] = set()
        for step in plan.steps:
            # Dependency check
            if not all(dep in completed for dep in step.depends_on):
                logger.warning(f"Skipping step {step.step_id} — dependencies not met: {step.depends_on}")
                self.tracer.fail_step(trace.trace_id, step.step_id, "Dependencies not met")
                ctx["warnings"].append(f"Step '{step.name}' skipped — dependencies unavailable.")
                continue

            self.tracer.start_step(trace.trace_id, step)
            t0 = time.time()

            try:
                step_out = self._execute_step(step, ctx, result)
                elapsed = time.time() - t0
                self.tracer.complete_step(
                    trace.trace_id, step.step_id,
                    output={"duration_s": round(elapsed, 3), **step_out},
                    warnings=ctx["warnings"][-3:]
                )
                completed.add(step.step_id)

            except Exception as e:
                logger.error(f"Step '{step.name}' failed: {e}")
                ctx["warnings"].append(f"Step '{step.name}' encountered an error: {str(e)[:200]}")
                self.tracer.fail_step(trace.trace_id, step.step_id, str(e))
                completed.add(step.step_id)  # Mark as done to not block later steps

        # Finalize result
        result.measurements = ctx["measurements"]
        result.warnings = list(set(ctx["warnings"]))
        result.layers = ctx["layers"]
        result.detections = ctx["detections"]

        # Estimate confidence
        conf = estimate_confidence(result.evidence_ids)
        result.confidence = conf.score
        result.confidence_level = conf.level

        self.tracer.complete_trace(trace.trace_id)
        return result

    # ─────────────────────────────────────────────────────────────────
    # STEP DISPATCH
    # ─────────────────────────────────────────────────────────────────

    def _execute_step(self, step, ctx: dict, result: OrchestratorResult) -> dict:
        """Dispatch a plan step to the right tool handler."""
        tool = step.tool
        params = step.parameters

        if tool == "ndvi":
            return self._run_ndvi(ctx, params, result)
        elif tool == "ndwi":
            return self._run_ndwi(ctx, params, result)
        elif tool == "landcover_analysis":
            return self._run_landcover(ctx, params, result)
        elif tool == "change_detection":
            return self._run_change_detection(ctx, params, result)
        elif tool == "image_registration":
            return self._run_registration(ctx, params, result)
        elif tool == "vqa":
            return self._run_vqa(ctx, params, result)
        elif tool == "captioning":
            return self._run_captioning(ctx, params, result)
        elif tool == "change_vqa":
            return self._run_change_vqa(ctx, params, result)
        elif tool == "grounding":
            return self._run_grounding(ctx, params, result)
        elif tool == "optical_sar_fusion":
            return self._run_optical_sar(ctx, params, result)
        elif tool == "area_calculator":
            return self._run_area(ctx, params, result)
        else:
            ctx["warnings"].append(f"Unknown tool '{tool}' in execution plan — skipped.")
            return {"skipped": True}

    # ─────────────────────────────────────────────────────────────────
    # INDIVIDUAL TOOL RUNNERS
    # ─────────────────────────────────────────────────────────────────

    def _run_ndvi(self, ctx, params, result):
        meta = ctx.get("meta_a")
        image = ctx.get("image_a")
        if image is None or meta is None:
            ctx["warnings"].append("NDVI: No image available.")
            return {"skipped": True}

        available = detect_available_indices(meta)
        if "ndvi" not in available or image.shape[-1] < 4:
            ctx["warnings"].append("NDVI: NIR or Red band not found — skipping NDVI calculation.")
            return {"skipped": True, "reason": "missing_bands"}

        ndvi_res = calculate_ndvi(image, red_band=2, nir_band=3, nodata=meta.nodata)
        if "ndvi" not in ndvi_res:
            return {"skipped": True}
        ndvi_array = ndvi_res["ndvi"]
        ndvi_stats = ndvi_res
        ctx["ndvi_stats"] = ndvi_stats

        # Colorize NDVI and save as layer
        layer_path = self._save_colormap_layer(
            ndvi_array, ctx["session_id"], "ndvi", cmap="RdYlGn"
        )
        if layer_path:
            ctx["layers"]["ndvi"] = f"/outputs/{layer_path.name}"

        # Measurements
        ctx["measurements"].append({
            "label": "Mean NDVI",
            "value": round(ndvi_stats.get("mean", 0), 4),
            "unit": "index",
            "evidence_type": "DERIVED"
        })
        ctx["measurements"].append({
            "label": "Vegetation Cover",
            "value": round(ndvi_stats.get("vegetation_fraction", 0) * 100, 2),
            "unit": "%",
            "evidence_type": "DERIVED"
        })

        # Evidence
        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.DERIVED,
            tool="ndvi",
            source="raster_computation",
            observation=f"NDVI mean={ndvi_stats.get('mean', 0):.4f}, vegetation fraction={ndvi_stats.get('vegetation_fraction', 0):.2%}",
            value=ndvi_stats,
            confidence=0.95
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"ndvi_mean": ndvi_stats.get("mean"), "vegetation_fraction": ndvi_stats.get("vegetation_fraction")}

    def _run_ndwi(self, ctx, params, result):
        meta = ctx.get("meta_a")
        image = ctx.get("image_a")
        if image is None or meta is None:
            ctx["warnings"].append("NDWI: No image available.")
            return {"skipped": True}

        available = detect_available_indices(meta)
        if "ndwi" not in available or image.shape[-1] < 4:
            ctx["warnings"].append("NDWI: Green or NIR band not found — skipping NDWI calculation.")
            return {"skipped": True, "reason": "missing_bands"}

        ndwi_res = calculate_ndwi(image, green_band=1, nir_band=3, nodata=meta.nodata)
        if "ndwi" not in ndwi_res:
            return {"skipped": True}
        ndwi_array = ndwi_res["ndwi"]
        ndwi_stats = ndwi_res
        ctx["ndwi_stats"] = ndwi_stats

        layer_path = self._save_colormap_layer(
            ndwi_array, ctx["session_id"], "ndwi", cmap="Blues"
        )
        if layer_path:
            ctx["layers"]["ndwi"] = f"/outputs/{layer_path.name}"

        ctx["measurements"].append({
            "label": "Mean NDWI",
            "value": round(ndwi_stats.get("mean", 0), 4),
            "unit": "index",
            "evidence_type": "DERIVED"
        })
        ctx["measurements"].append({
            "label": "Water Coverage",
            "value": round(ndwi_stats.get("water_fraction", 0) * 100, 2),
            "unit": "%",
            "evidence_type": "DERIVED"
        })

        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.DERIVED,
            tool="ndwi",
            source="raster_computation",
            observation=f"NDWI mean={ndwi_stats.get('mean', 0):.4f}, water fraction={ndwi_stats.get('water_fraction', 0):.2%}",
            value=ndwi_stats,
            confidence=0.93
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"ndwi_mean": ndwi_stats.get("mean"), "water_fraction": ndwi_stats.get("water_fraction")}

    def _run_landcover(self, ctx, params, result):
        image = ctx.get("image_a")
        meta = ctx.get("meta_a")
        if image is None or meta is None:
            return {"skipped": True}

        lc_result = perform_landcover_analysis(image, meta, n_clusters=params.get("n_clusters", 5))
        ctx["landcover"] = lc_result

        for cls, pct in lc_result.get("class_percentages", {}).items():
            ctx["measurements"].append({
                "label": f"{cls.title()} Area",
                "value": round(pct, 2),
                "unit": "%",
                "evidence_type": "DERIVED"
            })

        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.DERIVED,
            tool="landcover_kmeans",
            source="raster_computation",
            observation=f"K-Means land cover: {lc_result.get('class_percentages', {})}",
            value=lc_result,
            confidence=0.88
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"classes": list(lc_result.get("class_percentages", {}).keys())}

    def _run_change_detection(self, ctx, params, result):
        image_a = ctx.get("image_a")
        image_b = ctx.get("image_b")
        if image_a is None or image_b is None:
            ctx["warnings"].append("Change detection requires two images.")
            return {"skipped": True}

        meta_a = ctx.get("meta_a")
        meta_b = ctx.get("meta_b") or meta_a
        change_result = perform_change_detection(image_a, image_b, meta_a, meta_b)
        ctx["change_evidence"] = change_result

        change_pct = change_result.get("change_percentage", 0)
        changed_area = change_result.get("changed_area_km2", 0)

        ctx["measurements"].append({
            "label": "Changed Area",
            "value": round(change_pct, 2),
            "unit": "%",
            "evidence_type": "DETECTED"
        })
        if changed_area:
            ctx["measurements"].append({
                "label": "Changed Area (km²)",
                "value": round(changed_area, 4),
                "unit": "km²",
                "evidence_type": "DETECTED"
            })

        # Save change mask layer
        change_mask = change_result.get("change_mask")
        if change_mask is not None:
            layer_path = self._save_colormap_layer(
                change_mask.astype(float), ctx["session_id"], "change", cmap="hot"
            )
            if layer_path:
                ctx["layers"]["change"] = f"/outputs/{layer_path.name}"

        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.DETECTED,
            tool="change_vector_otsu",
            source="raster_computation",
            observation=f"Change detected: {change_pct:.2f}% of scene",
            value={"change_percentage": change_pct, "changed_area_km2": changed_area},
            confidence=0.91
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"change_percentage": change_pct, "changed_area_km2": changed_area}

    def _run_registration(self, ctx, params, result):
        image_a = ctx.get("image_a")
        image_b = ctx.get("image_b")
        meta_a = ctx.get("meta_a")
        meta_b = ctx.get("meta_b") or meta_a
        if image_a is None or image_b is None:
            return {"skipped": True}

        if meta_a and meta_b:
            compat_ok, _ = check_compatibility(meta_a, meta_b)
            if not compat_ok:
                ctx["warnings"].append("Registration: Images have incompatible spatial extents — using direct alignment.")

        reg_result = register_images(image_a, image_b)
        if reg_result.get("registered") is not None:
            ctx["image_b"] = reg_result["registered"]

        return {"quality_score": reg_result.get("quality_score", 0)}

    def _run_vqa(self, ctx, params, result):
        image = ctx.get("image_a")
        query = ctx.get("query", "Describe this satellite scene.")
        if image is None:
            return {"skipped": True}

        vqa_result = self.vlm.answer_question(
            image, query,
            context={"measurements": ctx["measurements"], "modality": ctx["modality"]}
        )
        result.answer = vqa_result.get("answer", "")

        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.AI_DETECTED,
            tool="vqa",
            source="Qwen2-VL-2B-Instruct+LoRA",
            observation=f"VLM Answer: {result.answer[:200]}",
            value={"answer": result.answer, "model": vqa_result.get("model")},
            confidence=vqa_result.get("confidence", 0.8) or 0.8
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"answer_length": len(result.answer)}

    def _run_captioning(self, ctx, params, result):
        image = ctx.get("image_a")
        if image is None:
            return {"skipped": True}

        cap_result = self.vlm.generate_caption(
            image,
            context={"measurements": ctx["measurements"], "modality": ctx["modality"]}
        )
        result.answer = cap_result.get("caption", "")

        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.AI_DETECTED,
            tool="captioning",
            source="Qwen2-VL-2B-Instruct+LoRA",
            observation=f"Caption: {result.answer[:200]}",
            value={"caption": result.answer},
            confidence=cap_result.get("confidence", 0.8) or 0.8
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"caption_length": len(result.answer)}

    def _run_change_vqa(self, ctx, params, result):
        image_a = ctx.get("image_a")
        image_b = ctx.get("image_b")
        if image_a is None or image_b is None:
            return {"skipped": True}

        change_ev = ctx.get("change_evidence", {})
        change_ev["question"] = ctx.get("query", "What changes occurred between these two dates?")

        vqa_result = self.vlm.explain_change(image_a, image_b, change_ev)
        result.answer = vqa_result.get("answer", "")

        rec = EvidenceRecord(
            session_id=ctx["session_id"],
            evidence_type=EvidenceType.AI_DETECTED,
            tool="change_vqa",
            source="Qwen2-VL-2B-Instruct+LoRA",
            observation=f"Change-VQA: {result.answer[:200]}",
            value={"answer": result.answer},
            confidence=vqa_result.get("confidence", 0.8) or 0.8
        )
        evidence_store.add(rec)
        result.evidence_ids.append(rec.id)

        return {"answer_length": len(result.answer)}

    def _run_grounding(self, ctx, params, result):
        image = ctx.get("image_a")
        query = ctx.get("query", "")
        if image is None:
            return {"skipped": True}

        # Extract target object from query
        prompt = query.replace("locate", "").replace("find", "").replace("where is", "").replace("show me", "").strip()
        if not prompt:
            prompt = "objects"

        # Run image in uint8 format
        if image.dtype != np.uint8:
            img_uint8 = (image[:, :, :min(3, image.shape[-1])] * 255).clip(0, 255).astype(np.uint8)
        else:
            img_uint8 = image[:, :, :min(3, image.shape[-1])]

        grounding_result = run_grounding(
            img_uint8, prompt,
            gdino_checkpoint=params.get("gdino_checkpoint", "models/grounding/gdino_1.5_edge.pth"),
            sam_checkpoint=params.get("sam_checkpoint", "models/segmentation/mobile_sam_v2.pt"),
            device="cpu"
        )

        ctx["detections"] = grounding_result.get("detections", [])
        ctx["warnings"].extend(grounding_result.get("warnings", []))

        if grounding_result.get("is_stub"):
            result.answer = (
                f"Grounding DINO models not yet downloaded. "
                f"Place `gdino_1.5_edge.pth` in `models/grounding/` and "
                f"`mobile_sam_v2.pt` in `models/segmentation/` to enable object detection."
            )
        else:
            n = len(ctx["detections"])
            labels = [d.get("label", "object") for d in ctx["detections"][:5]]
            result.answer = (
                f"Found {n} detection(s) for '{prompt}': {', '.join(labels)}. "
                f"Bounding boxes and polygon masks are available in the visualizer."
            )

        return {"n_detections": len(ctx["detections"])}

    def _run_optical_sar(self, ctx, params, result):
        from app.vision.optical_sar import analyze_optical_sar
        image_a = ctx.get("image_a")
        image_b = ctx.get("image_b")
        if image_a is None or image_b is None:
            return {"skipped": True}

        meta_a = ctx.get("meta_a")
        meta_b = ctx.get("meta_b")
        fusion_result = analyze_optical_sar(image_a, image_b, meta_a, meta_b)

        for key, val in fusion_result.get("measurements", {}).items():
            ctx["measurements"].append({
                "label": key,
                "value": val,
                "unit": "",
                "evidence_type": "DERIVED"
            })

        vqa_result = self.vlm.answer_question(
            image_a,
            ctx.get("query", "Describe what you observe in this multimodal satellite scene."),
            context={"measurements": ctx["measurements"], "modality": "optical+sar"}
        )
        result.answer = vqa_result.get("answer", "")

        return {"fusion_method": "feature_based"}

    def _run_area(self, ctx, params, result):
        meta = ctx.get("meta_a")
        if meta is None:
            return {"skipped": True}

        area_km2 = scene_area_km2(meta)
        if area_km2 is not None:
            ctx["measurements"].append({
                "label": "Scene Area",
                "value": round(area_km2, 4),
                "unit": "km²",
                "evidence_type": "DERIVED"
            })
        return {"scene_area_km2": area_km2}

    # ─────────────────────────────────────────────────────────────────
    # UTILITY: SAVE COLORMAP LAYER
    # ─────────────────────────────────────────────────────────────────

    def _save_colormap_layer(
        self, array: np.ndarray, session_id: str, name: str, cmap: str = "RdYlGn"
    ) -> Path | None:
        """Normalize a float raster array and save as a colored PNG overlay using Pillow."""
        try:
            from PIL import Image as PILImage

            arr = np.squeeze(array).astype(np.float32)
            if arr.ndim != 2:
                return None

            h, w = arr.shape
            rgba = np.zeros((h, w, 4), dtype=np.uint8)

            if cmap == "hot" or name == "change":
                # Red for change pixels, transparent elsewhere
                mask = arr > 0
                rgba[mask] = [239, 68, 68, 180]
            elif cmap == "Blues" or name == "ndwi":
                vmin, vmax = np.nanpercentile(arr, 2), np.nanpercentile(arr, 98)
                norm = np.clip((arr - vmin) / (vmax - vmin + 1e-6), 0, 1)
                rgba[:, :, 0] = (30 * norm).astype(np.uint8)
                rgba[:, :, 1] = (144 * norm).astype(np.uint8)
                rgba[:, :, 2] = (255 * norm).astype(np.uint8)
                rgba[:, :, 3] = (180 * norm).astype(np.uint8)
            else:
                # NDVI: Red -> Yellow -> Green
                vmin, vmax = np.nanpercentile(arr, 2), np.nanpercentile(arr, 98)
                norm = np.clip((arr - vmin) / (vmax - vmin + 1e-6), 0, 1)
                rgba[:, :, 0] = (255 * (1.0 - norm)).astype(np.uint8)
                rgba[:, :, 1] = (255 * norm).astype(np.uint8)
                rgba[:, :, 2] = 40
                rgba[:, :, 3] = 180

            img = PILImage.fromarray(rgba, mode="RGBA")
            filename = f"{session_id}_{name}_layer.png"
            path = self.output_dir / filename
            img.save(str(path))
            return path

        except Exception as e:
            logger.warning(f"Failed to save {name} colormap layer: {e}")
            return None
