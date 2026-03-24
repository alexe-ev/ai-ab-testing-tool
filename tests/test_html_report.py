"""Tests for html_report._build_cases_json(): context field inclusion."""

import json

from src.html_report import _build_cases_json


def _make_run_data(results):
    return {
        "results": results,
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
