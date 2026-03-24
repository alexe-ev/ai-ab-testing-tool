"""Tests for runner.py: per-prompt model resolution and context injection."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock, call

import yaml
import pytest

from src.runner import run_experiment


def _write_config(tmp_path, config_dict):
    p = os.path.join(tmp_path, "config.yaml")
    with open(p, "w") as f:
        yaml.dump(config_dict, f)
    return p


def _write_test_set(tmp_path, cases):
    p = os.path.join(tmp_path, "test_set.yaml")
    with open(p, "w") as f:
        yaml.dump({"test_cases": cases}, f)
    return p


def _make_mock_response(text="mock response"):
    return {
        "response": text,
        "input_tokens": 5,
        "output_tokens": 10,
        "latency_seconds": 0.1,
        "model": "gpt-4o-mini",
        "stop_reason": "end_turn",
    }


# ─── Per-prompt model tests ───────────────────────────────────────


def test_no_per_prompt_model_uses_global(tmp_path, sample_config, sample_test_cases):
    """Both prompts use the global model when no override is specified."""
    ts_path = _write_test_set(tmp_path, sample_test_cases[:1])
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    mock_client = MagicMock()
    with patch("src.runner.create_client", return_value=mock_client) as mock_create, \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    pm = output["config"]["prompt_models"]
    assert pm["prompt_a"] == "gpt-4o-mini"
    assert pm["prompt_b"] == "gpt-4o-mini"


def test_per_prompt_model_override_one_prompt(tmp_path, sample_test_cases):
    """Per-prompt model override on one prompt resolves correctly."""
    config = {
        "experiment": {"name": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "prompt_a": {"name": "A", "system": "You are A.", "model": "claude-sonnet-4-20250514"},
            "prompt_b": {"name": "B", "system": "You are B."},
        },
        "test_set": "",
        "rubric": "rubrics/support.yaml",
    }
    ts_path = _write_test_set(tmp_path, sample_test_cases[:1])
    config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, config)

    mock_client = MagicMock()
    with patch("src.runner.create_client", return_value=mock_client), \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    pm = output["config"]["prompt_models"]
    assert pm["prompt_a"] == "claude-sonnet-4-20250514"
    assert pm["prompt_b"] == "gpt-4o-mini"


def test_mixed_providers_creates_two_clients(tmp_path, sample_test_cases):
    """When prompts use different providers, two clients are created."""
    config = {
        "experiment": {"name": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A.", "model": "claude-sonnet-4-20250514"},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
        "test_set": "",
        "rubric": "rubrics/support.yaml",
    }
    ts_path = _write_test_set(tmp_path, sample_test_cases[:1])
    config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, config)

    mock_client = MagicMock()
    with patch("src.runner.create_client", return_value=mock_client) as mock_create, \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    # Two clients created: one for "anthropic", one for "openai"
    providers_called = {c.args[0] for c in mock_create.call_args_list}
    assert providers_called == {"anthropic", "openai"}
    assert mock_create.call_count == 2


def test_same_provider_different_models_creates_one_client(tmp_path, sample_test_cases):
    """Two prompts on the same provider but different models share one client."""
    config = {
        "experiment": {"name": "test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A.", "model": "gpt-4"},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
        "test_set": "",
        "rubric": "rubrics/support.yaml",
    }
    ts_path = _write_test_set(tmp_path, sample_test_cases[:1])
    config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, config)

    mock_client = MagicMock()
    with patch("src.runner.create_client", return_value=mock_client) as mock_create, \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    assert mock_create.call_count == 1


def test_prompt_models_saved_in_output_json(tmp_path, sample_config, sample_test_cases):
    """prompt_models dict is present and correct in output JSON."""
    ts_path = _write_test_set(tmp_path, sample_test_cases[:1])
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    assert "prompt_models" in output["config"]
    assert set(output["config"]["prompt_models"].keys()) == {"prompt_a", "prompt_b"}


# ─── Context injection tests ──────────────────────────────────────


def test_case_without_context_uses_raw_input(tmp_path, sample_config):
    """When a test case has no context, user_input passed to call_llm is raw input."""
    cases = [{"id": "c1", "category": "billing", "input": "Charge me twice."}]
    ts_path = _write_test_set(tmp_path, cases)
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    captured = []

    def capture_call(**kwargs):
        captured.append(kwargs["user_input"])
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    for user_input in captured:
        assert user_input == "Charge me twice."


def test_case_with_context_composes_input(tmp_path, sample_config):
    """When a test case has context, user_input is composed with the context block."""
    cases = [
        {
            "id": "c2",
            "category": "technical",
            "input": "Why is export broken?",
            "context": "User is on Pro plan.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    captured = []

    def capture_call(**kwargs):
        captured.append(kwargs["user_input"])
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    expected = (
        "[Retrieved context]\nUser is on Pro plan.\n\n"
        "[User question]\nWhy is export broken?"
    )
    for user_input in captured:
        assert user_input == expected


def test_context_saved_in_case_results(tmp_path, sample_config):
    """context field is saved in the case_results in the output JSON."""
    cases = [
        {
            "id": "c3",
            "category": "technical",
            "input": "My export is broken.",
            "context": "User is on Free plan.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    result = output["results"][0]
    assert result["context"] == "User is on Free plan."


def test_context_null_for_case_without_context(tmp_path, sample_config):
    """context field is null in output when test case has no context."""
    cases = [{"id": "c4", "category": "billing", "input": "Refund please."}]
    ts_path = _write_test_set(tmp_path, cases)
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    result = output["results"][0]
    assert result["context"] is None


def test_both_prompts_receive_same_composed_input(tmp_path, sample_config):
    """Both prompt_a and prompt_b receive the same composed user_input."""
    cases = [
        {
            "id": "c5",
            "category": "billing",
            "input": "Double charge.",
            "context": "Account in EU region.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    sample_config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, sample_config)

    captured = []

    def capture_call(**kwargs):
        captured.append(kwargs["user_input"])
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    # Two calls: one per prompt, both for the same case
    assert len(captured) == 2
    assert captured[0] == captured[1]
    assert "[Retrieved context]" in captured[0]
