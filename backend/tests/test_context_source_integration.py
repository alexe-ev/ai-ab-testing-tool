"""Integration tests for context_source: runner, pipeline_bridge, and API endpoint."""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import yaml
import pytest
from fastapi.testclient import TestClient

from src.runner import run_experiment, DEFAULT_CONTEXT_TEMPLATE
from src.context_source import ContextFetcher, ContextSourceError
from tests.conftest import write_config as _write_config, write_test_set as _write_test_set, make_mock_response as _make_mock_response


def _base_config():
    return {
        "experiment": {"name": "ctx-test"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "prompt_a": {"name": "A", "system": "You are A."},
            "prompt_b": {"name": "B", "system": "You are B."},
        },
        "rubric": "rubrics/support.yaml",
    }


# ─── Runner: dynamic context injected ────────────────────────────


def test_runner_dynamic_context_injected(tmp_path):
    """When context_source is in config and test case has no static context,
    dynamic context is fetched and injected."""
    cases = [{"id": "c1", "category": "general", "input": "What is X?"}]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    config["context_source"] = {"type": "script", "command": "echo fetched"}
    cfg_path = _write_config(tmp_path, config)

    captured_inputs = []

    def capture_call(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _make_mock_response()

    mock_fetcher = MagicMock(spec=ContextFetcher)
    mock_fetcher.fetch.return_value = "dynamic context content"

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call), \
         patch("src.runner.ContextFetcher", return_value=mock_fetcher):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    result = output["results"][0]
    assert result["context"] == "dynamic context content"
    assert result["context_source"] == "dynamic"
    assert "[Retrieved context]" in captured_inputs[0]
    assert "dynamic context content" in captured_inputs[0]


def test_runner_static_context_takes_priority(tmp_path):
    """Static context in test case overrides dynamic fetch; fetcher.fetch is not called."""
    cases = [
        {
            "id": "c2",
            "category": "general",
            "input": "Tell me about Y.",
            "context": "Static context here.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    config["context_source"] = {"type": "script", "command": "echo should_not_run"}
    cfg_path = _write_config(tmp_path, config)

    mock_fetcher = MagicMock(spec=ContextFetcher)
    mock_fetcher.fetch.return_value = "dynamic context content"

    captured_inputs = []

    def capture_call(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call), \
         patch("src.runner.ContextFetcher", return_value=mock_fetcher):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    result = output["results"][0]
    assert result["context"] == "Static context here."
    assert result["context_source"] == "static"
    mock_fetcher.fetch.assert_not_called()
    assert "Static context here." in captured_inputs[0]


def test_runner_context_source_fetch_error_stored(tmp_path):
    """When dynamic fetch fails, error is stored and context is None."""
    cases = [{"id": "c3", "category": "general", "input": "Question?"}]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    config["context_source"] = {"type": "script", "command": "false"}
    cfg_path = _write_config(tmp_path, config)

    mock_fetcher = MagicMock(spec=ContextFetcher)
    mock_fetcher.fetch.side_effect = ContextSourceError("Script failed")

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", return_value=_make_mock_response()), \
         patch("src.runner.ContextFetcher", return_value=mock_fetcher):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    result = output["results"][0]
    assert result["context"] is None
    assert result["context_source"] is None
    assert "Script failed" in result.get("context_fetch_error", "")


def test_runner_no_context_source_in_config(tmp_path):
    """When no context_source in config, context_source field is None for cases without context."""
    cases = [{"id": "c4", "category": "general", "input": "Hello."}]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    cfg_path = _write_config(tmp_path, config)

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", return_value=_make_mock_response()):
        out_path = run_experiment(cfg_path, output_dir=str(tmp_path))

    with open(out_path) as f:
        output = json.load(f)

    result = output["results"][0]
    assert result["context"] is None
    assert result["context_source"] is None


# ─── Pipeline bridge: context_source propagated ───────────────────


def test_pipeline_bridge_includes_context_source():
    """build_config_from_db includes context_source from experiment.config."""
    from src.api.pipeline_bridge import build_config_from_db

    context_source_cfg = {"type": "script", "command": "echo {input}"}

    experiment = MagicMock()
    experiment.name = "Test Experiment"
    experiment.config = {
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "a": {"name": "A", "system": "Sys A"},
            "b": {"name": "B", "system": "Sys B"},
        },
        "context_source": context_source_cfg,
    }

    test_set = MagicMock()
    test_set.cases = []

    rubric = MagicMock()
    rubric.dimensions = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("src.api.pipeline_bridge.OUTPUT_DIR", tmp_dir):
            config_path, ts_path, rubric_path = build_config_from_db(
                experiment, test_set, rubric, "claude-sonnet"
            )
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

    assert "context_source" in config_data
    assert config_data["context_source"] == context_source_cfg


def test_pipeline_bridge_no_context_source():
    """build_config_from_db omits context_source when not present."""
    from src.api.pipeline_bridge import build_config_from_db

    experiment = MagicMock()
    experiment.name = "Test Experiment"
    experiment.config = {
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "a": {"name": "A", "system": "Sys A"},
            "b": {"name": "B", "system": "Sys B"},
        },
    }

    test_set = MagicMock()
    test_set.cases = []

    rubric = MagicMock()
    rubric.dimensions = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("src.api.pipeline_bridge.OUTPUT_DIR", tmp_dir):
            config_path, ts_path, rubric_path = build_config_from_db(
                experiment, test_set, rubric, "claude-sonnet"
            )
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

    assert "context_source" not in config_data


# ─── API endpoint: /api/context-source/test ──────────────────────


def test_context_source_test_endpoint_success(client):
    """POST /api/context-source/test returns success with context."""
    mock_fetcher = MagicMock(spec=ContextFetcher)
    mock_fetcher.fetch.return_value = "fetched context"

    with patch("src.api.crud_routes.ContextFetcher", return_value=mock_fetcher):
        resp = client.post(
            "/api/context-source/test",
            json={"config": {"type": "script", "command": "echo {input}"}, "input_text": "hello"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["context"] == "fetched context"


def test_context_source_test_endpoint_error(client):
    """POST /api/context-source/test returns error on ContextSourceError."""
    mock_fetcher = MagicMock(spec=ContextFetcher)
    mock_fetcher.fetch.side_effect = ContextSourceError("Script crashed")

    with patch("src.api.crud_routes.ContextFetcher", return_value=mock_fetcher):
        resp = client.post(
            "/api/context-source/test",
            json={"config": {"type": "script", "command": "bad_cmd"}, "input_text": "hello"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Script crashed" in data["error"]


# ─── Context template and position tests ─────────────────────────


def test_runner_custom_context_template(tmp_path):
    """Custom context_template is applied when context is present."""
    cases = [
        {
            "id": "t1",
            "category": "general",
            "input": "What is Y?",
            "context": "Some static context.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    config["context_template"] = "<ctx>{context}</ctx>\n<q>{input}</q>"
    cfg_path = _write_config(tmp_path, config)

    captured_inputs = []

    def capture_call(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    expected = "<ctx>Some static context.</ctx>\n<q>What is Y?</q>"
    for user_input in captured_inputs:
        assert user_input == expected


def test_runner_context_position_system(tmp_path):
    """When context_position is 'system', context is appended to system prompt and user_input is raw."""
    cases = [
        {
            "id": "t2",
            "category": "general",
            "input": "Tell me about Z.",
            "context": "Relevant context here.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    config["context_position"] = "system"
    cfg_path = _write_config(tmp_path, config)

    captured_calls = []

    def capture_call(**kwargs):
        captured_calls.append({"system": kwargs["system_prompt"], "user": kwargs["user_input"]})
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    for call in captured_calls:
        # user_input must be the raw case input
        assert call["user"] == "Tell me about Z."
        # system prompt must contain the context
        assert "Relevant context here." in call["system"]
        # system prompt must have the original prompt system prefix
        assert "You are" in call["system"]


def test_runner_default_template_backward_compatible(tmp_path):
    """Without context_template or context_position in config, behavior matches old hardcoded format."""
    cases = [
        {
            "id": "t3",
            "category": "general",
            "input": "Old format question.",
            "context": "Old format context.",
        }
    ]
    ts_path = _write_test_set(tmp_path, cases)
    config = _base_config()
    config["test_set"] = ts_path
    # No context_template or context_position keys
    cfg_path = _write_config(tmp_path, config)

    captured_inputs = []

    def capture_call(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _make_mock_response()

    with patch("src.runner.create_client", return_value=MagicMock()), \
         patch("src.runner.call_llm", side_effect=capture_call):
        run_experiment(cfg_path, output_dir=str(tmp_path))

    expected = (
        "[Retrieved context]\nOld format context.\n\n"
        "[User question]\nOld format question."
    )
    for user_input in captured_inputs:
        assert user_input == expected


def test_pipeline_bridge_propagates_context_template(tmp_path):
    """build_config_from_db includes context_template and context_position when present."""
    from src.api.pipeline_bridge import build_config_from_db

    experiment = MagicMock()
    experiment.name = "Template Test"
    experiment.config = {
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "a": {"name": "A", "system": "Sys A"},
            "b": {"name": "B", "system": "Sys B"},
        },
        "context_template": "<ctx>{context}</ctx>\n<q>{input}</q>",
        "context_position": "system",
    }

    test_set = MagicMock()
    test_set.cases = []

    rubric = MagicMock()
    rubric.dimensions = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("src.api.pipeline_bridge.OUTPUT_DIR", tmp_dir):
            config_path, ts_path, rubric_path = build_config_from_db(
                experiment, test_set, rubric, "claude-sonnet"
            )
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

    assert config_data.get("context_template") == "<ctx>{context}</ctx>\n<q>{input}</q>"
    assert config_data.get("context_position") == "system"
