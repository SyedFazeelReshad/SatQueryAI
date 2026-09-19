from enum import Enum
from pydantic import BaseModel

class TaskType(str, Enum):
    SINGLE_VQA = "single_vqa"
    SINGLE_CAPTION = "single_caption"
    SINGLE_GROUNDING = "single_grounding"
    SINGLE_LANDCOVER = "single_landcover"
    CHANGE_DETECTION = "change_detection"
    CHANGE_VQA = "change_vqa"
    OPTICAL_SAR = "optical_sar"
    UNKNOWN = "unknown"

class InputConfig(BaseModel):
    n_images: int
    modalities: list[str]
    has_temporal_info: bool
    date_a: str | None = None
    date_b: str | None = None

class RouterResult(BaseModel):
    task_type: TaskType
    confidence: float
    reasoning: str
    suggested_tools: list[str]
    input_config: InputConfig

def route_query(query: str, input_config: InputConfig) -> RouterResult:
    q = query.lower()
    
    if input_config.n_images == 2:
        if "sar" in input_config.modalities and "optical" in input_config.modalities:
            return RouterResult(
                task_type=TaskType.OPTICAL_SAR,
                confidence=0.9,
                reasoning="Two images of different modalities detected.",
                suggested_tools=["optical_sar_analysis"],
                input_config=input_config
            )
        elif "change" in q or "difference" in q or "changed" in q:
            if "what" in q or "why" in q or "how" in q:
                return RouterResult(
                    task_type=TaskType.CHANGE_VQA,
                    confidence=0.8,
                    reasoning="Query asks question about changes between two images.",
                    suggested_tools=["change_detection", "change_vqa"],
                    input_config=input_config
                )
            else:
                return RouterResult(
                    task_type=TaskType.CHANGE_DETECTION,
                    confidence=0.9,
                    reasoning="Query asks for change detection between two images.",
                    suggested_tools=["change_detection"],
                    input_config=input_config
                )
                
    if input_config.n_images == 1:
        if "landcover" in q or "land cover" in q or "classes" in q or "classification" in q:
            return RouterResult(
                task_type=TaskType.SINGLE_LANDCOVER,
                confidence=0.85,
                reasoning="Query asks for land cover or class analysis.",
                suggested_tools=["landcover_analysis"],
                input_config=input_config
            )
        elif "highlight" in q or "where" in q or "find" in q or "locate" in q or "ground" in q or "show me" in q:
            return RouterResult(
                task_type=TaskType.SINGLE_GROUNDING,
                confidence=0.8,
                reasoning="Query asks to locate or highlight specific objects.",
                suggested_tools=["grounding"],
                input_config=input_config
            )
        elif "describe" in q or "caption" in q or ("what is" in q and "where" not in q):
            return RouterResult(
                task_type=TaskType.SINGLE_CAPTION,
                confidence=0.7,
                reasoning="Query asks for a description of the scene.",
                suggested_tools=["captioning"],
                input_config=input_config
            )
        elif "water" in q or "vegetation" in q or "built" in q:
            return RouterResult(
                task_type=TaskType.SINGLE_LANDCOVER,
                confidence=0.8,
                reasoning="Query asks for specific feature or land cover analysis.",
                suggested_tools=["landcover_analysis"],
                input_config=input_config
            )
        else:
            return RouterResult(
                task_type=TaskType.SINGLE_VQA,
                confidence=0.6,
                reasoning="Defaulting to VQA for general questions.",
                suggested_tools=["vqa"],
                input_config=input_config
            )

    return RouterResult(
        task_type=TaskType.UNKNOWN,
        confidence=0.0,
        reasoning="Cannot determine task type.",
        suggested_tools=[],
        input_config=input_config
    )
