"""
Pipeline bridge: connects DB entities to the file-based pipeline.

Converts Experiment / TestSet / Rubric DB objects into temp YAML files
and runs the full pipeline (runner -> evaluator -> analyzer -> reporter).
"""

import uuid
from pathlib import Path

import yaml

from src.runner import run_experiment
from src.evaluator import evaluate_run
from src.analyzer import analyze_evaluation
from src.reporter import generate_markdown_report, generate_summary_json
from src.html_report import generate_html_report
from src.api.jobs import update_job, update_job_progress


def build_config_from_db(experiment, test_set, rubric, judge_model: str) -> tuple[str, str, str]:
    """
    Convert DB entities into temp YAML files and a config dict.

    Returns (config_path, test_set_path, rubric_path) — paths to temp files.
    Caller is responsible for deleting them after use.
    """
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)

    tmp_id = str(uuid.uuid4())[:8]

    # Build test set YAML
    test_cases = []
    for case in test_set.cases:
        entry = {
            "id": case.case_identifier or case.id,
            "category": case.category or "",
            "input": case.input,
        }
        if case.context:
            entry["context"] = case.context
        if case.reference:
            entry["reference"] = case.reference
        test_cases.append(entry)

    test_set_data = {"test_cases": test_cases}
    test_set_path = str(output_dir / f"_tmp_test_set_{tmp_id}.yaml")
    with open(test_set_path, "w") as f:
        yaml.dump(test_set_data, f, allow_unicode=True)

    # Build rubric YAML
    dimensions = []
    for dim in rubric.dimensions:
        levels = dim.levels if isinstance(dim.levels, list) else []
        dimensions.append({
            "name": dim.name,
            "description": dim.description or "",
            "weight": float(dim.weight),
            "levels": levels,
        })

    rubric_data = {"dimensions": dimensions}
    rubric_path = str(output_dir / f"_tmp_rubric_{tmp_id}.yaml")
    with open(rubric_path, "w") as f:
        yaml.dump(rubric_data, f, allow_unicode=True)

    # Build config dict
    exp_config = experiment.config or {}
    config = {
        "experiment": {"name": experiment.name},
        "model": exp_config.get("model", {"name": "gpt-4o", "temperature": 0.3, "max_tokens": 1024}),
        "prompts": exp_config.get("prompts", {}),
        "test_set": test_set_path,
        "rubric": rubric_path,
        "judge": {"model": judge_model},
        "output": {"dir": "results"},
    }

    config_path = str(output_dir / f"_tmp_config_{tmp_id}.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f, allow_unicode=True)

    return config_path, test_set_path, rubric_path


def run_full_pipeline(
    config_path: str,
    test_set_path: str,
    rubric_path: str,
    output_dir: str,
    mode: str,
    judge_model: str,
    job_id: str,
) -> None:
    """
    Run the full pipeline in a background thread.

    Steps: run -> evaluate -> analyze -> report.
    Updates job progress at each step.
    On error, marks job as failed.
    """
    try:
        # Step 1: run
        update_job_progress(job_id, {"step": "running", "detail": "Executing prompts against test cases"})
        run_results_path = run_experiment(config_path, output_dir)

        # Step 2: evaluate
        update_job_progress(job_id, {"step": "evaluating", "detail": "Scoring responses with judge model"})
        eval_path = evaluate_run(run_results_path, rubric_path, output_dir, mode, judge_model)

        # Step 3: analyze
        update_job_progress(job_id, {"step": "analyzing", "detail": "Computing statistics"})
        analysis_path = analyze_evaluation(eval_path, output_dir, run_path=run_results_path)

        # Step 4: report
        update_job_progress(job_id, {"step": "reporting", "detail": "Generating reports"})
        report_path = generate_markdown_report(analysis_path, run_results_path, output_dir)
        summary_path = generate_summary_json(analysis_path, output_dir)
        html_path = generate_html_report(analysis_path, run_results_path, eval_path, output_dir)

        update_job(
            job_id,
            "done",
            result={
                "run_path": run_results_path,
                "eval_path": eval_path,
                "analysis_path": analysis_path,
                "report_path": report_path,
                "summary_path": summary_path,
                "html_path": html_path,
            },
        )
    except Exception as e:
        update_job(job_id, "failed", error=str(e))
    finally:
        # Clean up temp files
        for path in [config_path, test_set_path, rubric_path]:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                pass
