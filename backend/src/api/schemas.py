from typing import Any, Optional
from pydantic import BaseModel


# ─── Request models ───────────────────────────────────────────────

class RunRequest(BaseModel):
    config: dict[str, Any]


class EvaluateRequest(BaseModel):
    run_id: str
    rubric_path: str
    mode: str = "both"
    judge_model: str = "claude-sonnet-4-20250514"


class AnalyzeRequest(BaseModel):
    eval_id: str


# ─── Response models ──────────────────────────────────────────────

class JobResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DryRunResponse(BaseModel):
    valid: bool
    experiment_name: str
    model: str
    prompt_names: list[str]
    prompt_models: dict[str, str]
    test_case_count: int
    estimated_calls: int


class ResultsResponse(BaseModel):
    run_id: str
    run_data: Optional[dict[str, Any]] = None
    eval_data: Optional[dict[str, Any]] = None
    analysis: Optional[dict[str, Any]] = None
