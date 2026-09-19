from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import uuid

class TraceStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class TraceStep(BaseModel):
    step_id: str
    name: str
    tool: str
    parameters: dict
    status: TraceStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_s: float | None = None
    output_summary: dict = {}
    warnings: list[str] = []
    error: str | None = None

class ExecutionTrace(BaseModel):
    trace_id: str
    session_id: str
    task_type: str
    started_at: datetime
    completed_at: datetime | None = None
    total_duration_s: float | None = None
    steps: list[TraceStep]
    status: TraceStatus

class ExecutionTracer:
    def __init__(self):
        self.traces: dict[str, ExecutionTrace] = {}

    def start_trace(self, session_id: str, task_type: str) -> ExecutionTrace:
        trace_id = str(uuid.uuid4())
        trace = ExecutionTrace(
            trace_id=trace_id,
            session_id=session_id,
            task_type=task_type,
            started_at=datetime.utcnow(),
            steps=[],
            status=TraceStatus.RUNNING
        )
        self.traces[trace_id] = trace
        return trace

    def start_step(self, trace_id: str, step) -> None:
        trace = self.traces.get(trace_id)
        if trace:
            trace_step = TraceStep(
                step_id=step.step_id,
                name=step.name,
                tool=step.tool,
                parameters=step.parameters,
                status=TraceStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            trace.steps.append(trace_step)

    def complete_step(self, trace_id: str, step_id: str, output: dict, warnings: list[str]) -> None:
        trace = self.traces.get(trace_id)
        if trace:
            for step in trace.steps:
                if step.step_id == step_id:
                    step.status = TraceStatus.SUCCESS
                    step.completed_at = datetime.utcnow()
                    step.duration_s = (step.completed_at - step.started_at).total_seconds()
                    step.output_summary = output
                    step.warnings = warnings
                    break

    def fail_step(self, trace_id: str, step_id: str, error: str) -> None:
        trace = self.traces.get(trace_id)
        if trace:
            for step in trace.steps:
                if step.step_id == step_id:
                    step.status = TraceStatus.FAILED
                    step.completed_at = datetime.utcnow()
                    step.duration_s = (step.completed_at - step.started_at).total_seconds()
                    step.error = error
                    break
            trace.status = TraceStatus.FAILED
            trace.completed_at = datetime.utcnow()
            trace.total_duration_s = (trace.completed_at - trace.started_at).total_seconds()

    def complete_trace(self, trace_id: str) -> ExecutionTrace | None:
        trace = self.traces.get(trace_id)
        if trace:
            if trace.status != TraceStatus.FAILED:
                trace.status = TraceStatus.SUCCESS
            trace.completed_at = datetime.utcnow()
            trace.total_duration_s = (trace.completed_at - trace.started_at).total_seconds()
        return trace

    def get_trace(self, trace_id: str) -> ExecutionTrace | None:
        return self.traces.get(trace_id)
