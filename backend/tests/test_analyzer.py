"""Tests for analyzer.py: compute_operational_metrics()."""

import pytest

from src.analyzer import compute_operational_metrics


def _make_run_data(
    prompt_keys=None,
    models=None,
    responses_by_case=None,
):
    """Build minimal run_data dict for testing."""
    if prompt_keys is None:
        prompt_keys = ["prompt_a", "prompt_b"]
    if models is None:
        models = {k: "gpt-4o-mini" for k in prompt_keys}
    prompt_names = {k: k.replace("_", " ").title() for k in prompt_keys}

    results = []
    if responses_by_case:
        for i, resp_map in enumerate(responses_by_case):
            results.append({
                "test_case_id": f"case-{i+1:03d}",
                "category": "test",
                "input": f"Question {i+1}",
                "context": None,
                "responses": resp_map,
            })

    return {
        "run_id": "test_run",
        "config": {
            "experiment": {"name": "test"},
            "model": {"name": "gpt-4o-mini"},
            "prompt_names": prompt_names,
            "prompt_models": models,
        },
        "results": results,
        "summary": {"total_cases": len(results)},
    }


def _resp(latency=0.5, input_tokens=100, output_tokens=200, model="gpt-4o-mini"):
    return {
        "response": "Test response.",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_seconds": latency,
        "model": model,
        "stop_reason": "end_turn",
    }


# ─── Basic metrics ────────────────────────────────────────────────


def test_operational_metrics_basic():
    """Correct avg/p50/p95 latency from mock run data."""
    run_data = _make_run_data(
        responses_by_case=[
            {"prompt_a": _resp(latency=1.0), "prompt_b": _resp(latency=2.0)},
            {"prompt_a": _resp(latency=2.0), "prompt_b": _resp(latency=3.0)},
            {"prompt_a": _resp(latency=3.0), "prompt_b": _resp(latency=4.0)},
        ]
    )

    result = compute_operational_metrics(run_data)
    assert "per_prompt" in result
    pp_a = result["per_prompt"]["prompt_a"]
    pp_b = result["per_prompt"]["prompt_b"]

    # Prompt A: latencies [1.0, 2.0, 3.0]
    assert pp_a["latency"]["avg"] == pytest.approx(2.0, abs=0.01)
    assert pp_a["latency"]["p50"] == pytest.approx(2.0, abs=0.01)
    assert pp_a["latency"]["p95"] == pytest.approx(2.9, abs=0.1)

    # Prompt B: latencies [2.0, 3.0, 4.0]
    assert pp_b["latency"]["avg"] == pytest.approx(3.0, abs=0.01)


def test_operational_metrics_token_totals():
    """Total and avg tokens are computed correctly."""
    run_data = _make_run_data(
        responses_by_case=[
            {"prompt_a": _resp(input_tokens=100, output_tokens=200),
             "prompt_b": _resp(input_tokens=50, output_tokens=100)},
            {"prompt_a": _resp(input_tokens=100, output_tokens=200),
             "prompt_b": _resp(input_tokens=50, output_tokens=100)},
        ]
    )

    result = compute_operational_metrics(run_data)
    pp_a = result["per_prompt"]["prompt_a"]
    pp_b = result["per_prompt"]["prompt_b"]

    assert pp_a["tokens"]["total_input"] == 200
    assert pp_a["tokens"]["total_output"] == 400
    assert pp_a["tokens"]["total"] == 600
    assert pp_a["tokens"]["avg_per_response"] == pytest.approx(300.0, abs=0.1)

    assert pp_b["tokens"]["total"] == 300


def test_operational_metrics_cost():
    """Cost is computed when model is in pricing table."""
    run_data = _make_run_data(
        models={"prompt_a": "gpt-4o-mini", "prompt_b": "gpt-4o-mini"},
        responses_by_case=[
            {"prompt_a": _resp(input_tokens=1_000_000, output_tokens=0, model="gpt-4o-mini"),
             "prompt_b": _resp(input_tokens=1_000_000, output_tokens=0, model="gpt-4o-mini")},
        ]
    )

    result = compute_operational_metrics(run_data)
    pp_a = result["per_prompt"]["prompt_a"]
    # gpt-4o-mini: $0.15 per 1M input
    assert pp_a["cost_usd"] is not None
    assert abs(pp_a["cost_usd"] - 0.15) < 1e-4


def test_operational_metrics_unknown_model_cost_none():
    """Unknown model has cost_usd = None."""
    run_data = _make_run_data(
        models={"prompt_a": "unknown-model", "prompt_b": "unknown-model"},
        responses_by_case=[
            {"prompt_a": _resp(), "prompt_b": _resp()},
        ]
    )

    result = compute_operational_metrics(run_data)
    assert result["per_prompt"]["prompt_a"]["cost_usd"] is None


# ─── Multi-variable warning ───────────────────────────────────────


def test_operational_metrics_multi_variable_warning():
    """multi_variable_warning is True when models differ between prompts."""
    run_data = _make_run_data(
        models={"prompt_a": "gpt-4o-mini", "prompt_b": "claude-sonnet-4-20250514"},
        responses_by_case=[
            {"prompt_a": _resp(model="gpt-4o-mini"),
             "prompt_b": _resp(model="claude-sonnet-4-20250514")},
        ]
    )

    result = compute_operational_metrics(run_data)
    assert result["multi_variable_warning"] is True


def test_operational_metrics_no_warning_same_model():
    """multi_variable_warning is False when both prompts use the same model."""
    run_data = _make_run_data(
        models={"prompt_a": "gpt-4o-mini", "prompt_b": "gpt-4o-mini"},
        responses_by_case=[
            {"prompt_a": _resp(), "prompt_b": _resp()},
        ]
    )

    result = compute_operational_metrics(run_data)
    assert result["multi_variable_warning"] is False


def test_operational_metrics_empty_results():
    """No results produce None latency and zero tokens."""
    run_data = _make_run_data(responses_by_case=[])

    result = compute_operational_metrics(run_data)
    pp_a = result["per_prompt"]["prompt_a"]
    assert pp_a["latency"]["avg"] is None
    assert pp_a["tokens"]["total"] == 0
    assert pp_a["n_responses"] == 0


def test_operational_metrics_model_name_in_per_prompt():
    """Model name is correctly stored per prompt."""
    run_data = _make_run_data(
        models={"prompt_a": "gpt-4o", "prompt_b": "claude-haiku-3"},
        responses_by_case=[
            {"prompt_a": _resp(model="gpt-4o"), "prompt_b": _resp(model="claude-haiku-3")},
        ]
    )

    result = compute_operational_metrics(run_data)
    assert result["per_prompt"]["prompt_a"]["model"] == "gpt-4o"
    assert result["per_prompt"]["prompt_b"]["model"] == "claude-haiku-3"
