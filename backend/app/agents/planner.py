"""
SatQuery AI — Upgraded Execution Planner (Stage 3)

Produces rich, multi-step execution plans based on query routing results.
Each plan is a dependency-resolved DAG of tool calls.
"""

from pydantic import BaseModel
from app.agents.router import RouterResult, InputConfig, TaskType
import uuid


class ExecutionStep(BaseModel):
    step_id: str
    name: str
    tool: str
    parameters: dict
    depends_on: list[str]


class ExecutionPlan(BaseModel):
    plan_id: str
    task_type: TaskType
    steps: list[ExecutionStep]
    estimated_duration_s: float


def create_plan(router_result: RouterResult, input_config: InputConfig) -> ExecutionPlan:
    """
    Generate a multi-step execution plan from the router result.

    Stage 3 plans compose multiple tools in dependency order:
    - Registration → Change Detection → Change-VQA → Report
    - NDVI → NDWI → Landcover → VQA → Report
    - Grounding → VQA → Report
    - Optical-SAR Fusion → VQA → Report
    """
    steps = []
    has_two_images = getattr(input_config, "has_secondary_image", False)

    task = router_result.task_type

    # ──────────────────────────────────────────────────────
    # CHANGE DETECTION: Register → Change → Area → VLM Explanation
    # ──────────────────────────────────────────────────────
    if task == TaskType.CHANGE_DETECTION:
        steps = [
            ExecutionStep(
                step_id="s1", name="Register bi-temporal images",
                tool="image_registration", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="Compute change mask (CVA + Otsu)",
                tool="change_detection", parameters={"method": "otsu"}, depends_on=["s1"]
            ),
            ExecutionStep(
                step_id="s3", name="Measure changed area",
                tool="area_calculator", parameters={}, depends_on=["s2"]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # CHANGE VQA: Register → Change → VLM Explanation
    # ──────────────────────────────────────────────────────
    elif task == TaskType.CHANGE_VQA:
        steps = [
            ExecutionStep(
                step_id="s1", name="Register bi-temporal images",
                tool="image_registration", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="Compute change mask (CVA + Otsu)",
                tool="change_detection", parameters={"method": "otsu"}, depends_on=["s1"]
            ),
            ExecutionStep(
                step_id="s3", name="Measure changed area",
                tool="area_calculator", parameters={}, depends_on=["s2"]
            ),
            ExecutionStep(
                step_id="s4", name="VLM change explanation",
                tool="change_vqa", parameters={}, depends_on=["s2", "s3"]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # LAND COVER: NDVI → NDWI → Landcover → VQA
    # ──────────────────────────────────────────────────────
    elif task == TaskType.SINGLE_LANDCOVER:
        steps = [
            ExecutionStep(
                step_id="s1", name="Compute NDVI vegetation index",
                tool="ndvi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="Compute NDWI water index",
                tool="ndwi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s3", name="K-Means land cover clustering",
                tool="landcover_analysis", parameters={"n_clusters": 5}, depends_on=["s1", "s2"]
            ),
            ExecutionStep(
                step_id="s4", name="VLM land cover description",
                tool="vqa", parameters={}, depends_on=["s3"]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # VQA: NDVI → NDWI → VLM Answer
    # ──────────────────────────────────────────────────────
    elif task == TaskType.SINGLE_VQA:
        steps = [
            ExecutionStep(
                step_id="s1", name="Compute NDVI (vegetation context)",
                tool="ndvi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="Compute NDWI (water context)",
                tool="ndwi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s3", name="VLM answer with deterministic context",
                tool="vqa", parameters={}, depends_on=["s1", "s2"]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # CAPTIONING: NDVI → NDWI → Scene Caption
    # ──────────────────────────────────────────────────────
    elif task == TaskType.SINGLE_CAPTION:
        steps = [
            ExecutionStep(
                step_id="s1", name="Compute NDVI",
                tool="ndvi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="Compute NDWI",
                tool="ndwi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s3", name="Scene area measurement",
                tool="area_calculator", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s4", name="VLM scene captioning",
                tool="captioning", parameters={}, depends_on=["s1", "s2", "s3"]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # GROUNDING: NDVI context → Object Detection → Grounding VLM
    # ──────────────────────────────────────────────────────
    elif task == TaskType.SINGLE_GROUNDING:
        steps = [
            ExecutionStep(
                step_id="s1", name="Compute NDVI (scene context)",
                tool="ndvi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="Text-guided object detection (Grounding DINO + MobileSAM)",
                tool="grounding", parameters={}, depends_on=["s1"]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # OPTICAL+SAR FUSION: Fusion → VLM Cross-Modal Explanation
    # ──────────────────────────────────────────────────────
    elif task == TaskType.OPTICAL_SAR:
        steps = [
            ExecutionStep(
                step_id="s1", name="Optical-SAR feature fusion",
                tool="optical_sar_fusion", parameters={}, depends_on=[]
            ),
        ]

    # ──────────────────────────────────────────────────────
    # FALLBACK: generic NDVI + VQA
    # ──────────────────────────────────────────────────────
    else:
        steps = [
            ExecutionStep(
                step_id="s1", name="Compute spectral indices",
                tool="ndvi", parameters={}, depends_on=[]
            ),
            ExecutionStep(
                step_id="s2", name="VLM general answer",
                tool="vqa", parameters={}, depends_on=["s1"]
            ),
        ]

    return ExecutionPlan(
        plan_id=str(uuid.uuid4()),
        task_type=router_result.task_type,
        steps=steps,
        estimated_duration_s=round(8.0 * len(steps), 1)
    )
