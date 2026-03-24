import json
import re
import threading
import tempfile
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from src.api.jobs import create_job, update_job, get_job
from src.api.schemas import (
    RunRequest,
    EvaluateRequest,
    AnalyzeRequest,
    JobResponse,
    JobStatusResponse,
    DryRunResponse,
    ResultsResponse,
)
from src.runner import run_experiment, load_config, load_test_set
from src.evaluator import evaluate_run
from src.analyzer import analyze_evaluation
from src.reporter import generate_markdown_report, generate_summary_json
from src.html_report import generate_html_report

router = APIRouter(prefix="/api")

OUTPUT_DIR = "results"


def _validate_id(value: str, name: str = "id") -> str:
    if not re.fullmatch(r'[\w-]+', value):
        raise HTTPException(status_code=400, detail=f"Invalid {name}")
    return value


def _safe_rubric_path(rubric_path: str) -> str:
    base = Path("rubrics").resolve()
    resolved = (base / Path(rubric_path).name).resolve()
    if not str(resolved).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid rubric path")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Rubric not found")
    return str(resolved)


# ─── Health ───────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok"}


# ─── Dry run ──────────────────────────────────────────────────────

@router.post("/experiments/dry-run", response_model=DryRunResponse)
def dry_run(req: RunRequest):
    config = req.config

    # Validate required keys
    required = ["experiment", "model", "prompts", "test_set", "rubric"]
    missing = [k for k in required if k not in config]
    if missing:
        raise HTTPException(status_code=422, detail=f"Config missing required keys: {missing}")

    prompts = config.get("prompts", {})
    if len(prompts) < 2:
        raise HTTPException(status_code=422, detail="Need at least 2 prompts")

    # Load test set to get case count
    test_set_path = config["test_set"]
    try:
        test_cases = load_test_set(test_set_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Cannot load test set: {e}")

    model_cfg = config["model"]
    default_model = model_cfg.get("name", "")

    prompt_models = {}
    for key, pcfg in prompts.items():
        m = pcfg.get("model", default_model)
        prompt_models[key] = m

    # Write config to temp file and do a dry run to validate it loads correctly
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp:
        yaml.dump(config, tmp)
        tmp_path = tmp.name

    try:
        run_experiment(tmp_path, OUTPUT_DIR, dry_run=True)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Config validation failed: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return DryRunResponse(
        valid=True,
        experiment_name=config["experiment"].get("name", "unnamed"),
        model=default_model,
        prompt_names=list(prompts.keys()),
        prompt_models=prompt_models,
        test_case_count=len(test_cases),
        estimated_calls=len(test_cases) * len(prompts),
    )


# ─── Run (async) ──────────────────────────────────────────────────

@router.post("/experiments/run", response_model=JobResponse, status_code=202)
def start_run(req: RunRequest):
    job_id = create_job()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp:
        yaml.dump(req.config, tmp)
        tmp_path = tmp.name

    def _run():
        try:
            update_job(job_id, "running")
            result_path = run_experiment(tmp_path, OUTPUT_DIR)
            # Extract run_id from filename: results/run_{run_id}.json
            run_id = Path(result_path).stem.removeprefix("run_")
            update_job(job_id, "done", result={"run_id": run_id, "path": result_path})
        except Exception as e:
            update_job(job_id, "failed", error=str(e))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    return JobResponse(job_id=job_id, status="pending")


# ─── Evaluate (async) ─────────────────────────────────────────────

@router.post("/experiments/{run_id}/evaluate", response_model=JobResponse, status_code=202)
def start_evaluate(run_id: str, req: EvaluateRequest):
    _validate_id(run_id, "run_id")
    safe_rubric = _safe_rubric_path(req.rubric_path)
    # Find the run file
    run_files = list(Path(OUTPUT_DIR).glob(f"run_{run_id}*.json"))
    if not run_files:
        raise HTTPException(status_code=404, detail=f"Run file not found for run_id: {run_id}")
    results_path = str(run_files[0])

    job_id = create_job()

    def _evaluate():
        try:
            update_job(job_id, "running")
            eval_path = evaluate_run(
                results_path,
                safe_rubric,
                OUTPUT_DIR,
                req.mode,
                req.judge_model,
            )
            eval_id = Path(eval_path).stem.removeprefix("eval_")
            update_job(job_id, "done", result={"eval_id": eval_id, "path": eval_path})
        except Exception as e:
            update_job(job_id, "failed", error=str(e))

    t = threading.Thread(target=_evaluate, daemon=True)
    t.start()

    return JobResponse(job_id=job_id, status="pending")


# ─── Analyze (sync) ───────────────────────────────────────────────

@router.post("/experiments/{run_id}/analyze")
def analyze(run_id: str):
    _validate_id(run_id, "run_id")
    eval_files = list(Path(OUTPUT_DIR).glob(f"eval_{run_id}*.json"))
    if not eval_files:
        raise HTTPException(status_code=404, detail=f"Eval file not found for run_id: {run_id}")
    eval_path = str(eval_files[0])

    try:
        analysis_path = analyze_evaluation(eval_path, OUTPUT_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    with open(analysis_path) as f:
        analysis_data = json.load(f)

    return analysis_data


# ─── Report (sync) ────────────────────────────────────────────────

@router.post("/experiments/{run_id}/report")
def report(run_id: str):
    _validate_id(run_id, "run_id")
    run_files = list(Path(OUTPUT_DIR).glob(f"run_{run_id}*.json"))
    eval_files = list(Path(OUTPUT_DIR).glob(f"eval_{run_id}*.json"))
    analysis_files = list(Path(OUTPUT_DIR).glob(f"analysis_{run_id}*.json"))

    if not run_files:
        raise HTTPException(status_code=404, detail=f"Run file not found for run_id: {run_id}")
    if not eval_files:
        raise HTTPException(status_code=404, detail=f"Eval file not found for run_id: {run_id}")
    if not analysis_files:
        raise HTTPException(status_code=404, detail=f"Analysis file not found for run_id: {run_id}")

    run_path = str(run_files[0])
    eval_path = str(eval_files[0])
    analysis_path = str(analysis_files[0])

    try:
        report_path = generate_markdown_report(analysis_path, run_path, OUTPUT_DIR)
        summary_path = generate_summary_json(analysis_path, OUTPUT_DIR)
        html_path = generate_html_report(analysis_path, run_path, eval_path, OUTPUT_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "report_path": report_path,
        "summary_path": summary_path,
        "html_path": html_path,
    }


# ─── Results (sync) ───────────────────────────────────────────────

@router.get("/experiments/{run_id}/results", response_model=ResultsResponse)
def get_results(run_id: str):
    _validate_id(run_id, "run_id")
    run_files = list(Path(OUTPUT_DIR).glob(f"run_{run_id}*.json"))
    if not run_files:
        raise HTTPException(status_code=404, detail=f"No results found for run_id: {run_id}")

    run_data = None
    eval_data = None
    analysis_data = None

    with open(run_files[0]) as f:
        run_data = json.load(f)

    eval_files = list(Path(OUTPUT_DIR).glob(f"eval_{run_id}*.json"))
    if eval_files:
        with open(eval_files[0]) as f:
            eval_data = json.load(f)

    analysis_files = list(Path(OUTPUT_DIR).glob(f"analysis_{run_id}*.json"))
    if analysis_files:
        with open(analysis_files[0]) as f:
            analysis_data = json.load(f)

    return ResultsResponse(
        run_id=run_id,
        run_data=run_data,
        eval_data=eval_data,
        analysis=analysis_data,
    )


# ─── Job status ───────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobStatusResponse(job_id=job_id, **job)
