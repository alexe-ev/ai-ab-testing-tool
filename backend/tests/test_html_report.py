"""Tests for html_report: _build_cases_json(), model names, performance section, warning."""

import json
import os
import tempfile

from src.html_report import _build_cases_json, generate_html_report


def _make_run_data(results, model_a="gpt-4o-mini", model_b="gpt-4o-mini"):
    return {
        "run_id": "test_run",
        "config": {
            "experiment": {"name": "Test"},
            "model": {"name": model_a},
            "prompt_names": {"prompt_a": "Minimal", "prompt_b": "Detailed"},
            "prompt_models": {"prompt_a": model_a, "prompt_b": model_b},
        },
        "results": results,
        "summary": {"total_cases": len(results), "total_calls": len(results) * 2, "errors": 0},
    }


def _make_eval_data(evaluations=None):
    return {
        "evaluations": evaluations or [],
    }


def _make_analysis(key_a="prompt_a", key_b="prompt_b"):
    return {
        "prompt_a": {"key": key_a, "name": "Minimal"},
        "prompt_b": {"key": key_b, "name": "Detailed"},
    }


def _make_full_analysis_data(
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
                    "name": "Minimal",
                    "model": model_a,
                    "n_responses": 2,
                    "latency": {"avg": 1.0, "p50": 0.9, "p95": 1.5},
                    "tokens": {"total_input": 200, "total_output": 400, "total": 600, "avg_per_response": 300.0},
                    "cost_usd": 0.00033,
                },
                "prompt_b": {
                    "name": "Detailed",
                    "model": model_b,
                    "n_responses": 2,
                    "latency": {"avg": 2.0, "p50": 1.9, "p95": 2.8},
                    "tokens": {"total_input": 200, "total_output": 400, "total": 600, "avg_per_response": 300.0},
                    "cost_usd": 0.009 if "claude-sonnet" in model_b else 0.00033,
                },
            },
            "multi_variable_warning": multi_variable_warning,
        }

    analysis = {
        "prompt_a": {"key": "prompt_a", "name": "Minimal"},
        "prompt_b": {"key": "prompt_b", "name": "Detailed"},
        "recommendation": {"winner": "Minimal", "confidence": "high", "signals": {}},
    }
    if op_metrics:
        analysis["operational_metrics"] = op_metrics

    return {
        "analysis_id": "analysis_test_001",
        "eval_id": "eval_test_001",
        "run_id": "test_run",
        "timestamp": "2026-03-24T10:00:00+00:00",
        "analysis": analysis,
    }


def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


# ─── context field ────────────────────────────────────────────────


def test_build_cases_json_includes_context_field():
    """Cases with context have the context value in the JSON output."""
    run_data = _make_run_data([
        {
            "test_case_id": "c1",
            "category": "technical",
            "input": "Why is export broken?",
            "context": "User is on Pro plan.",
            "responses": {
                "prompt_a": {"response": "Check settings.", "input_tokens": 5, "output_tokens": 10, "latency_seconds": 0.1},
                "prompt_b": {"response": "Try again.", "input_tokens": 5, "output_tokens": 10, "latency_seconds": 0.1},
            },
        }
    ])

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert len(cases) == 1
    assert cases[0]["context"] == "User is on Pro plan."


def test_build_cases_json_context_null_when_absent():
    """Cases without context have context: null in the JSON output."""
    run_data = _make_run_data([
        {
            "test_case_id": "c2",
            "category": "billing",
            "input": "Refund please.",
            "context": None,
            "responses": {
                "prompt_a": {"response": "Processing.", "input_tokens": 5, "output_tokens": 10, "latency_seconds": 0.1},
                "prompt_b": {"response": "Done.", "input_tokens": 5, "output_tokens": 10, "latency_seconds": 0.1},
            },
        }
    ])

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["context"] is None


def test_build_cases_json_context_null_when_key_missing():
    """Cases where context key is entirely absent also produce context: null."""
    run_data = _make_run_data([
        {
            "test_case_id": "c3",
            "category": "billing",
            "input": "Cancel subscription.",
            # no "context" key at all
            "responses": {
                "prompt_a": {"response": "OK.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
                "prompt_b": {"response": "Sure.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
            },
        }
    ])

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["context"] is None


def test_build_cases_json_mixed_cases():
    """Handles a mix of cases with and without context correctly."""
    run_data = _make_run_data([
        {
            "test_case_id": "c1",
            "category": "billing",
            "input": "Question A.",
            "context": "Some context.",
            "responses": {
                "prompt_a": {"response": "Resp A1.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
                "prompt_b": {"response": "Resp B1.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
            },
        },
        {
            "test_case_id": "c2",
            "category": "billing",
            "input": "Question B.",
            "context": None,
            "responses": {
                "prompt_a": {"response": "Resp A2.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
                "prompt_b": {"response": "Resp B2.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
            },
        },
    ])

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["context"] == "Some context."
    assert cases[1]["context"] is None


def test_build_cases_json_scores_included_when_eval_present():
    """When eval data exists for a case, scores_a and scores_b are included."""
    run_data = _make_run_data([
        {
            "test_case_id": "c1",
            "category": "billing",
            "input": "Question.",
            "context": None,
            "responses": {
                "prompt_a": {"response": "A resp.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
                "prompt_b": {"response": "B resp.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
            },
        }
    ])

    eval_data = _make_eval_data([
        {
            "test_case_id": "c1",
            "pointwise": {
                "prompt_a": {"accuracy": {"score": 4, "reasoning": "Good."}},
                "prompt_b": {"accuracy": {"score": 3, "reasoning": "Average."}},
            },
        }
    ])

    result_json = _build_cases_json(run_data, eval_data, _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["scores_a"] == {"accuracy": {"score": 4, "reasoning": "Good."}}
    assert cases[0]["scores_b"] == {"accuracy": {"score": 3, "reasoning": "Average."}}


def test_build_cases_json_scores_none_when_no_eval():
    """When no eval data exists for a case, scores_a and scores_b are None."""
    run_data = _make_run_data([
        {
            "test_case_id": "c1",
            "category": "billing",
            "input": "Question.",
            "context": None,
            "responses": {
                "prompt_a": {"response": "A resp.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
                "prompt_b": {"response": "B resp.", "input_tokens": 5, "output_tokens": 5, "latency_seconds": 0.1},
            },
        }
    ])

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["scores_a"] is None
    assert cases[0]["scores_b"] is None


# ─── Model name in cases JSON ─────────────────────────────────────


def test_html_response_viewer_shows_model():
    """Model name is present per response in the cases JSON."""
    run_data = _make_run_data(
        results=[
            {
                "test_case_id": "c1",
                "category": "billing",
                "input": "Question.",
                "context": None,
                "responses": {
                    "prompt_a": {
                        "response": "A resp.",
                        "input_tokens": 5,
                        "output_tokens": 5,
                        "latency_seconds": 0.1,
                        "model": "gpt-4o-mini",
                    },
                    "prompt_b": {
                        "response": "B resp.",
                        "input_tokens": 5,
                        "output_tokens": 5,
                        "latency_seconds": 0.1,
                        "model": "claude-sonnet-4-20250514",
                    },
                },
            }
        ],
        model_a="gpt-4o-mini",
        model_b="claude-sonnet-4-20250514",
    )

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["responses"]["prompt_a"]["model"] == "gpt-4o-mini"
    assert cases[0]["responses"]["prompt_b"]["model"] == "claude-sonnet-4-20250514"


def test_html_response_viewer_fallback_model_from_config():
    """When response has no model field, it is populated from prompt_models config."""
    run_data = _make_run_data(
        results=[
            {
                "test_case_id": "c1",
                "category": "billing",
                "input": "Question.",
                "context": None,
                "responses": {
                    "prompt_a": {
                        "response": "A resp.",
                        "input_tokens": 5,
                        "output_tokens": 5,
                        "latency_seconds": 0.1,
                        # no "model" key
                    },
                    "prompt_b": {
                        "response": "B resp.",
                        "input_tokens": 5,
                        "output_tokens": 5,
                        "latency_seconds": 0.1,
                        # no "model" key
                    },
                },
            }
        ],
        model_a="gpt-4o",
        model_b="gpt-4o-mini",
    )

    result_json = _build_cases_json(run_data, _make_eval_data(), _make_analysis())
    cases = json.loads(result_json)

    assert cases[0]["responses"]["prompt_a"]["model"] == "gpt-4o"
    assert cases[0]["responses"]["prompt_b"]["model"] == "gpt-4o-mini"


# ─── Full HTML generation tests ───────────────────────────────────


def _make_minimal_results():
    return [
        {
            "test_case_id": "c1",
            "category": "billing",
            "input": "Question?",
            "context": None,
            "responses": {
                "prompt_a": {"response": "Resp A.", "input_tokens": 10, "output_tokens": 20, "latency_seconds": 1.0, "model": "gpt-4o-mini"},
                "prompt_b": {"response": "Resp B.", "input_tokens": 10, "output_tokens": 20, "latency_seconds": 2.0, "model": "claude-sonnet-4-20250514"},
            },
        }
    ]


def test_html_header_shows_per_prompt_models():
    """Per-prompt model names appear in the HTML header."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        eval_path = os.path.join(tmpdir, "eval.json")

        _write_json(analysis_path, _make_full_analysis_data(
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
        ))
        _write_json(run_path, _make_run_data(
            _make_minimal_results(),
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
        ))
        _write_json(eval_path, _make_eval_data())

        html_path = generate_html_report(analysis_path, run_path, eval_path, tmpdir)
        content = open(html_path).read()

        # Both model names must appear in header meta
        assert "gpt-4o-mini" in content
        assert "claude-sonnet-4-20250514" in content


def test_html_has_performance_section():
    """Performance section with latency/cost is present in HTML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        eval_path = os.path.join(tmpdir, "eval.json")

        _write_json(analysis_path, _make_full_analysis_data())
        _write_json(run_path, _make_run_data(_make_minimal_results()))
        _write_json(eval_path, _make_eval_data())

        html_path = generate_html_report(analysis_path, run_path, eval_path, tmpdir)
        content = open(html_path).read()

        assert "perf-section" in content
        assert "Performance" in content
        assert "Latency" in content
        assert "Cost" in content


def test_html_warning_banner():
    """Warning div is present when multi_variable_warning is True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        eval_path = os.path.join(tmpdir, "eval.json")

        _write_json(analysis_path, _make_full_analysis_data(
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
            multi_variable_warning=True,
        ))
        _write_json(run_path, _make_run_data(
            _make_minimal_results(),
            model_a="gpt-4o-mini",
            model_b="claude-sonnet-4-20250514",
        ))
        _write_json(eval_path, _make_eval_data())

        html_path = generate_html_report(analysis_path, run_path, eval_path, tmpdir)
        content = open(html_path).read()

        assert "warning-banner" in content
        assert "Multi-variable" in content


def test_html_no_warning_when_false():
    """Warning message absent when multi_variable_warning is False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        analysis_path = os.path.join(tmpdir, "analysis.json")
        run_path = os.path.join(tmpdir, "run.json")
        eval_path = os.path.join(tmpdir, "eval.json")

        _write_json(analysis_path, _make_full_analysis_data(multi_variable_warning=False))
        _write_json(run_path, _make_run_data(_make_minimal_results()))
        _write_json(eval_path, _make_eval_data())

        html_path = generate_html_report(analysis_path, run_path, eval_path, tmpdir)
        content = open(html_path).read()

        assert "Multi-variable" not in content
