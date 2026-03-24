"""Tests for reporter.py: per-prompt model display, performance sections, warning banner."""

import json
import os
import tempfile

import pytest

from src.reporter import generate_markdown_report, generate_summary_json


# ─── Fixtures ─────────────────────────────────────────────────────

def _make_analysis_data(
    name_a="Minimal",
    name_b="Detailed",
    model_a="gpt-4o-mini",
    model_b="gpt-4o-mini",
    multi_variable_warning=False,
    include_operational_metrics=True,
):
    op_metrics = None
    if include_operational_metrics:
        op_metrics = {
            "per_prompt": {
                "prompt_a": {
                    "name": name_a,
                    "model": model_a,
                    "n_responses": 3,
                    "latency": {"avg": 1.200, "p50": 1.100, "p95": 1.800},
                    "tokens": {"total_input": 300, "total_output": 600, "total": 900, "avg_per_response": 300.0},
                    "cost_usd": 0.000495,
                },
                "prompt_b": {
                    "name": name_b,
                    "model": model_b,
                    "n_responses": 3,
                    "latency": {"avg": 2.500, "p50": 2.400, "p95": 3.100},
                    "tokens": {"total_input": 300, "total_output": 600, "total": 900, "avg_per_response": 300.0},
                    "cost_usd": 0.012 if model_b == "claude-sonnet-4-20250514" else 0.000495,
                },
            },
            "multi_variable_warning": multi_variable_warning,
        }

    analysis = {
        "prompt_a": {"key": "prompt_a", "name": name_a},
        "prompt_b": {"key": "prompt_b", "name": name_b},
        "recommendation": {"winner": name_a, "confidence": "high", "signals": {"for_a": 2, "for_b": 0}},
    }
    if op_metrics:
        analysis["operational_metrics"] = op_metrics

    return {
        "analysis_id": "analysis_test_run_001",
        "eval_id": "eval_test_run_001",
        "run_id": "test_run_001",
        "timestamp": "2026-03-24T10:00:00+00:00",
        "analysis": analysis,
    }


def _make_run_data(model_a="gpt-4o-mini", model_b="gpt-4o-mini"):
    return {
        "run_id": "test_run_001",
        "config": {
            "experiment": {"name": "Test Experiment"},
            "model": {"name": "gpt-4o-mini"},
            "prompt_names": {"prompt_a": "Minimal", "prompt_b": "Detailed"},
            "prompt_models": {"prompt_a": model_a, "prompt_b": model_b},
        },
        "results": [],
        "summary": {"total_cases": 5, "total_calls": 10, "errors": 0},
    }


def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


# ─── Markdown: per-prompt model display ──────────────────────────


def test_markdown_shows_per_prompt_models():
    """Model names for each prompt appear in the markdown output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        _write_json(analysis_path, _make_analysis_data(model_a="gpt-4o-mini", model_b="claude-sonnet-4-20250514"))
        _write_json(run_path, _make_run_data(model_a="gpt-4o-mini", model_b="claude-sonnet-4-20250514"))

        report_path = generate_markdown_report(analysis_path, run_path, tmpdir)
        content = open(report_path).read()

        assert "gpt-4o-mini" in content
        assert "claude-sonnet-4-20250514" in content


def test_markdown_shows_latency_comparison():
    """avg/p50/p95 latency values appear in the markdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        _write_json(analysis_path, _make_analysis_data())
        _write_json(run_path, _make_run_data())

        report_path = generate_markdown_report(analysis_path, run_path, tmpdir)
        content = open(report_path).read()

        assert "Latency" in content
        assert "Avg" in content
        assert "p50" in content
        assert "p95" in content
        assert "1.200s" in content
        assert "2.500s" in content


def test_markdown_shows_warning_banner():
    """Warning text is present when multi_variable_warning is True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        _write_json(analysis_path, _make_analysis_data(
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
            multi_variable_warning=True,
        ))
        _write_json(run_path, _make_run_data(
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
        ))

        report_path = generate_markdown_report(analysis_path, run_path, tmpdir)
        content = open(report_path).read()

        assert "Warning" in content
        assert "model" in content.lower()


def test_markdown_no_warning_when_false():
    """Warning text absent when multi_variable_warning is False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        _write_json(analysis_path, _make_analysis_data(multi_variable_warning=False))
        _write_json(run_path, _make_run_data())

        report_path = generate_markdown_report(analysis_path, run_path, tmpdir)
        content = open(report_path).read()

        assert "Multi-variable" not in content


# ─── Summary JSON ─────────────────────────────────────────────────


def test_summary_json_includes_models():
    """models dict is present in summary JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        _write_json(analysis_path, _make_analysis_data(
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
        ))

        summary_path = generate_summary_json(analysis_path, tmpdir)
        summary = json.loads(open(summary_path).read())

        assert "models" in summary
        assert summary["models"]["prompt_a"] == "gpt-4o-mini"
        assert summary["models"]["prompt_b"] == "claude-sonnet-4-20250514"


def test_summary_json_includes_operational_metrics():
    """operational_metrics key present in summary JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        _write_json(analysis_path, _make_analysis_data())

        summary_path = generate_summary_json(analysis_path, tmpdir)
        summary = json.loads(open(summary_path).read())

        assert "operational_metrics" in summary


# ─── Backward compatibility ───────────────────────────────────────


def test_backward_compat_no_operational_metrics():
    """Report renders without error when operational_metrics is absent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        _write_json(analysis_path, _make_analysis_data(include_operational_metrics=False))
        _write_json(run_path, _make_run_data())

        # Should not raise
        report_path = generate_markdown_report(analysis_path, run_path, tmpdir)
        content = open(report_path).read()

        # Falls back to global model
        assert "gpt-4o-mini" in content

        # Summary also works
        summary_path = generate_summary_json(analysis_path, tmpdir)
        summary = json.loads(open(summary_path).read())
        assert "recommendation" in summary


def test_summary_no_models_when_no_operational_metrics():
    """models key absent from summary when operational_metrics not present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        _write_json(analysis_path, _make_analysis_data(include_operational_metrics=False))

        summary_path = generate_summary_json(analysis_path, tmpdir)
        summary = json.loads(open(summary_path).read())

        assert "models" not in summary
        assert "operational_metrics" not in summary
