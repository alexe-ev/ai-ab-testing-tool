import os
import threading
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
import json
from pathlib import Path

from src.db.engine import get_db
from src.db import crud
from src.api.jobs import create_job
from src.api.pipeline_bridge import build_config_from_db, run_full_pipeline
from src.api.routes import _validate_id


# ─── Request / Response schemas ───────────────────────────────────

class TestCaseIn(BaseModel):
    case_identifier: str
    category: str = ""
    input: str
    context: Optional[str] = None
    reference: Optional[str] = None


class TestSetCreate(BaseModel):
    name: str
    cases: list[TestCaseIn] = []


class TestCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_identifier: str
    category: str
    input: str
    context: Optional[str]
    reference: Optional[str]


class TestSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    cases: list[TestCaseOut] = []


class TestSetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    case_count: int


class RubricLevelIn(BaseModel):
    score: int
    description: str


class RubricDimensionIn(BaseModel):
    name: str
    description: str = ""
    weight: float = 0.0
    levels: list[RubricLevelIn] = []


class RubricCreate(BaseModel):
    name: str
    dimensions: list[RubricDimensionIn] = []


class RubricDimensionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    weight: float
    levels: Any
    sort_order: int


class RubricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    dimensions: list[RubricDimensionOut] = []


class RubricListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class ExperimentCreate(BaseModel):
    name: str
    description: str = ""
    hypothesis: str = ""
    config: Optional[dict] = None


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    hypothesis: str
    config: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class ExperimentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    hypothesis: str
    run_count: int
    last_run_at: Optional[datetime] = None
    last_run_metrics: Optional[dict] = None


class RunHistoryItem(BaseModel):
    id: str
    experiment_id: Optional[str] = None
    experiment_name: Optional[str] = None
    status: str
    prompt_names: dict
    prompt_models: dict
    total_cases: int
    error_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    summary_metrics: Optional[dict] = None


class RunHistoryResponse(BaseModel):
    items: list[RunHistoryItem]
    total: int


# ─── Test Sets router ─────────────────────────────────────────────

test_sets_router = APIRouter(prefix="/api/test-sets", tags=["test-sets"])


@test_sets_router.post("/", status_code=201, response_model=TestSetOut)
def create_test_set(body: TestSetCreate, db: Session = Depends(get_db)):
    ts = crud.create_test_set(
        db,
        name=body.name,
        cases=[c.model_dump() for c in body.cases],
    )
    return ts


@test_sets_router.get("/", response_model=list[TestSetListItem])
def list_test_sets(db: Session = Depends(get_db)):
    rows = crud.list_test_sets(db)
    return [
        TestSetListItem(id=ts.id, name=ts.name, case_count=case_count)
        for ts, case_count in rows
    ]


@test_sets_router.get("/{id}", response_model=TestSetOut)
def get_test_set(id: str, db: Session = Depends(get_db)):
    ts = crud.get_test_set(db, id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Test set not found")
    return ts


@test_sets_router.put("/{id}", response_model=TestSetOut)
def update_test_set(id: str, body: TestSetCreate, db: Session = Depends(get_db)):
    ts = crud.update_test_set(
        db,
        id=id,
        name=body.name,
        cases=[c.model_dump() for c in body.cases],
    )
    if ts is None:
        raise HTTPException(status_code=404, detail="Test set not found")
    return ts


@test_sets_router.delete("/{id}", status_code=204)
def delete_test_set(id: str, db: Session = Depends(get_db)):
    deleted = crud.delete_test_set(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test set not found")


# ─── Rubrics router ───────────────────────────────────────────────

rubrics_router = APIRouter(prefix="/api/rubrics", tags=["rubrics"])


@rubrics_router.post("/", status_code=201, response_model=RubricOut)
def create_rubric(body: RubricCreate, db: Session = Depends(get_db)):
    rubric = crud.create_rubric(
        db,
        name=body.name,
        dimensions=[d.model_dump() for d in body.dimensions],
    )
    return rubric


@rubrics_router.get("/", response_model=list[RubricListItem])
def list_rubrics(db: Session = Depends(get_db)):
    return crud.list_rubrics(db)


@rubrics_router.get("/{id}", response_model=RubricOut)
def get_rubric(id: str, db: Session = Depends(get_db)):
    rubric = crud.get_rubric(db, id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric


@rubrics_router.put("/{id}", response_model=RubricOut)
def update_rubric(id: str, body: RubricCreate, db: Session = Depends(get_db)):
    rubric = crud.update_rubric(
        db,
        id=id,
        name=body.name,
        dimensions=[d.model_dump() for d in body.dimensions],
    )
    if rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return rubric


@rubrics_router.delete("/{id}", status_code=204)
def delete_rubric(id: str, db: Session = Depends(get_db)):
    deleted = crud.delete_rubric(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rubric not found")


# ─── Experiments router ───────────────────────────────────────────

experiments_db_router = APIRouter(prefix="/api/experiments-db", tags=["experiments-db"])


@experiments_db_router.post("/", status_code=201, response_model=ExperimentOut)
def create_experiment(body: ExperimentCreate, db: Session = Depends(get_db)):
    return crud.create_experiment(
        db,
        name=body.name,
        description=body.description,
        hypothesis=body.hypothesis,
        config=body.config,
    )


@experiments_db_router.get("/", response_model=list[ExperimentListItem])
def list_experiments(db: Session = Depends(get_db)):
    rows = crud.list_experiments_with_last_run(db)
    return [
        ExperimentListItem(
            id=exp.id,
            name=exp.name,
            description=exp.description,
            hypothesis=exp.hypothesis,
            run_count=run_count,
            last_run_at=last_run_at,
            last_run_metrics=last_run_metrics if last_run_metrics else None,
        )
        for exp, run_count, last_run_at, last_run_metrics in rows
    ]


@experiments_db_router.get("/{id}", response_model=ExperimentOut)
def get_experiment(id: str, db: Session = Depends(get_db)):
    exp = crud.get_experiment(db, id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@experiments_db_router.put("/{id}", response_model=ExperimentOut)
def update_experiment(id: str, body: ExperimentCreate, db: Session = Depends(get_db)):
    exp = crud.update_experiment(
        db,
        id=id,
        name=body.name,
        description=body.description,
        hypothesis=body.hypothesis,
        config=body.config,
    )
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@experiments_db_router.delete("/{id}", status_code=204)
def delete_experiment(id: str, db: Session = Depends(get_db)):
    deleted = crud.delete_experiment(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Experiment not found")


# ─── Run schemas ───────────────────────────────────────────────────

class DryRunRequest(BaseModel):
    test_set_id: str
    rubric_id: str


class DryRunResult(BaseModel):
    valid: bool
    experiment_name: str
    test_case_count: int
    prompt_names: list[str]
    prompt_models: dict
    rubric_name: str


class RunFullRequest(BaseModel):
    test_set_id: str
    rubric_id: str
    judge_model: str = "claude-sonnet-4-20250514"
    mode: str = "both"


class RunFullResponse(BaseModel):
    job_id: str
    status: str


# ─── Shared validation helper ─────────────────────────────────────

def _load_experiment_resources(db: Session, experiment_id: str, test_set_id: str, rubric_id: str):
    """Fetch and validate experiment, test set, and rubric. Raises HTTPException on any missing resource."""
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    test_set = crud.get_test_set(db, test_set_id)
    if test_set is None:
        raise HTTPException(status_code=404, detail="Test set not found")

    rubric = crud.get_rubric(db, rubric_id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="Rubric not found")

    return experiment, test_set, rubric


# ─── Run endpoints ────────────────────────────────────────────────

@experiments_db_router.post("/{id}/dry-run", response_model=DryRunResult)
def dry_run_experiment(id: str, body: DryRunRequest, db: Session = Depends(get_db)):
    experiment, test_set, rubric = _load_experiment_resources(db, id, body.test_set_id, body.rubric_id)

    exp_config = experiment.config or {}
    prompts = exp_config.get("prompts", {})
    if len(prompts) < 2:
        raise HTTPException(status_code=422, detail="Experiment needs at least 2 prompts in config")

    default_model = exp_config.get("model", {}).get("name", "")
    prompt_models = {
        key: (pcfg.get("model", default_model) if isinstance(pcfg, dict) else default_model)
        for key, pcfg in prompts.items()
    }

    return DryRunResult(
        valid=True,
        experiment_name=experiment.name,
        test_case_count=len(test_set.cases),
        prompt_names=list(prompts.keys()),
        prompt_models=prompt_models,
        rubric_name=rubric.name,
    )


@experiments_db_router.post("/{id}/run-full", response_model=RunFullResponse, status_code=202)
def run_full_experiment(id: str, body: RunFullRequest, db: Session = Depends(get_db)):
    experiment, test_set, rubric = _load_experiment_resources(db, id, body.test_set_id, body.rubric_id)

    exp_config = experiment.config or {}
    prompts = exp_config.get("prompts", {})
    if len(prompts) < 2:
        raise HTTPException(status_code=422, detail="Experiment needs at least 2 prompts in config")

    if not test_set.cases:
        raise HTTPException(status_code=422, detail="Test set has no cases")

    config_path, test_set_path, rubric_path = build_config_from_db(
        experiment, test_set, rubric, body.judge_model
    )

    job_id = create_job()

    def _run():
        run_full_pipeline(
            config_path=config_path,
            test_set_path=test_set_path,
            rubric_path=rubric_path,
            output_dir="results",
            mode=body.mode,
            judge_model=body.judge_model,
            job_id=job_id,
            experiment_id=experiment.id,
        )

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return RunFullResponse(job_id=job_id, status="pending")


# ─── Run list + results schemas ───────────────────────────────────

class RunListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    prompt_names: dict
    prompt_models: dict
    total_cases: int
    error_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class RunResultsResponse(BaseModel):
    run_id: str
    run_data: Optional[dict] = None
    eval_data: Optional[dict] = None
    analysis: Optional[dict] = None


# ─── Experiment runs sub-resource ─────────────────────────────────

@experiments_db_router.get("/{id}/runs", response_model=list[RunListItem])
def list_runs(id: str, db: Session = Depends(get_db)):
    exp = crud.get_experiment(db, id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return crud.list_experiment_runs(db, id)


# ─── Runs router ──────────────────────────────────────────────────

runs_router = APIRouter(prefix="/api/runs", tags=["runs"])


@runs_router.get("/", response_model=RunHistoryResponse)
def list_all_runs(
    experiment_id: Optional[str] = None,
    status: Optional[str] = None,
    model: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    rows, total = crud.list_runs(
        db,
        experiment_id=experiment_id,
        status=status,
        model=model,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    items = [
        RunHistoryItem(
            id=run.id,
            experiment_id=run.experiment_id,
            experiment_name=exp_name,
            status=run.status,
            prompt_names=run.prompt_names or {},
            prompt_models=run.prompt_models or {},
            total_cases=run.total_cases,
            error_count=run.error_count,
            created_at=run.created_at,
            completed_at=run.completed_at,
            summary_metrics=run.summary_metrics if run.summary_metrics else None,
        )
        for run, exp_name in rows
    ]
    return RunHistoryResponse(items=items, total=total)


@runs_router.get("/{run_id}/results", response_model=RunResultsResponse)
def get_run_results(run_id: str, db: Session = Depends(get_db)):
    _validate_id(run_id, "run_id")
    run = crud.get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    output_dir = Path("results")
    run_data = eval_data = analysis = None

    run_files = list(output_dir.glob(f"run_{run_id}*.json"))
    if run_files:
        with open(run_files[0]) as f:
            run_data = json.load(f)

    eval_files = list(output_dir.glob(f"eval_{run_id}*.json"))
    if eval_files:
        with open(eval_files[0]) as f:
            eval_data = json.load(f)

    analysis_files = list(output_dir.glob(f"analysis_{run_id}*.json"))
    if analysis_files:
        with open(analysis_files[0]) as f:
            analysis = json.load(f)

    return RunResultsResponse(run_id=run_id, run_data=run_data, eval_data=eval_data, analysis=analysis)


@runs_router.get("/{run_id}/export/{format}")
def export_run(run_id: str, format: str, db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse

    _validate_id(run_id, "run_id")
    run = crud.get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    output_dir = Path("results")
    format_map = {
        "html": (f"report_{run_id}*.html", "text/html"),
        "markdown": (f"report_{run_id}*.md", "text/markdown"),
        "json": (f"summary_{run_id}*.json", "application/json"),
    }
    if format not in format_map:
        raise HTTPException(status_code=422, detail=f"Invalid format: {format}. Must be html, markdown, or json")

    pattern, media_type = format_map[format]
    files = list(output_dir.glob(pattern))
    if not files:
        raise HTTPException(status_code=404, detail=f"Report file not found for format: {format}")

    return FileResponse(str(files[0]), media_type=media_type, filename=files[0].name)


# ─── Settings router ─────────────────────────────────────────────

ALLOWED_SETTINGS = {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}

settings_router = APIRouter(prefix="/api/settings", tags=["settings"])


def _mask_key(value: str) -> str:
    if len(value) <= 8:
        return "****"
    return value[:4] + "****" + value[-4:]


class SettingOut(BaseModel):
    key: str
    value: str
    is_set: bool


class SettingsUpdate(BaseModel):
    key: str
    value: str


@settings_router.get("/", response_model=list[SettingOut])
def get_settings(db: Session = Depends(get_db)):
    result = []
    for key in sorted(ALLOWED_SETTINGS):
        setting = crud.get_setting(db, key)
        if setting:
            result.append(SettingOut(key=key, value=_mask_key(setting.value), is_set=True))
        else:
            env_val = os.environ.get(key, "")
            if env_val:
                result.append(SettingOut(key=key, value=_mask_key(env_val), is_set=True))
            else:
                result.append(SettingOut(key=key, value="", is_set=False))
    return result


@settings_router.put("/", response_model=SettingOut)
def update_setting(body: SettingsUpdate, db: Session = Depends(get_db)):
    if body.key not in ALLOWED_SETTINGS:
        raise HTTPException(status_code=422, detail=f"Unknown setting: {body.key}")
    if not body.value.strip():
        raise HTTPException(status_code=422, detail="Value cannot be empty")

    crud.upsert_setting(db, body.key, body.value.strip())
    os.environ[body.key] = body.value.strip()

    return SettingOut(key=body.key, value=_mask_key(body.value.strip()), is_set=True)


@settings_router.delete("/{key}", status_code=204)
def delete_setting(key: str, db: Session = Depends(get_db)):
    if key not in ALLOWED_SETTINGS:
        raise HTTPException(status_code=422, detail=f"Unknown setting: {key}")
    crud.delete_setting(db, key)
    os.environ.pop(key, None)
