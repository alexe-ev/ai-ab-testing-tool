"""Tests for cli.require_api_key(): provider detection with per-prompt models."""

import os
from unittest.mock import patch

import pytest
import click

from src.cli import require_api_key


def _env_with(**kwargs):
    """Build a minimal environment dict with specified keys set."""
    return {k: v for k, v in kwargs.items()}


# ─── Global model only ────────────────────────────────────────────


def test_global_openai_model_checks_openai_key():
    """Global gpt- model requires OPENAI_API_KEY."""
    config = {
        "model": {"name": "gpt-4o-mini"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A."},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
        # Should not raise
        require_api_key(config)


def test_global_anthropic_model_checks_anthropic_key():
    """Global claude- model requires ANTHROPIC_API_KEY."""
    config = {
        "model": {"name": "claude-sonnet-4-20250514"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A."},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True):
        require_api_key(config)


def test_global_model_missing_key_raises():
    """When the required key is missing, raises ClickException (which causes SystemExit)."""
    config = {
        "model": {"name": "gpt-4o-mini"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A."},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(click.ClickException):
            require_api_key(config)


# ─── Per-prompt model overrides ───────────────────────────────────


def test_per_prompt_override_adds_provider_check():
    """Per-prompt override adds the overriding provider to the required set."""
    config = {
        "model": {"name": "gpt-4o-mini"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A.", "model": "claude-sonnet-4-20250514"},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": "sk-ant-test"},
        clear=True,
    ):
        # Both keys present, should not raise
        require_api_key(config)


def test_per_prompt_override_missing_provider_key_raises():
    """Missing key for a per-prompt override provider raises ClickException."""
    config = {
        "model": {"name": "gpt-4o-mini"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A.", "model": "claude-sonnet-4-20250514"},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    # Only OPENAI_API_KEY set; ANTHROPIC_API_KEY missing
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
        with pytest.raises(click.ClickException) as exc_info:
            require_api_key(config)

    assert "ANTHROPIC_API_KEY" in str(exc_info.value.format_message())


def test_per_prompt_same_provider_does_not_duplicate_check():
    """Two prompts using the same provider still require only one key check."""
    config = {
        "model": {"name": "gpt-4o-mini"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A.", "model": "gpt-4"},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
        # Should not raise — both are openai, one key is enough
        require_api_key(config)


def test_missing_key_for_one_of_two_providers_raises():
    """When both providers are needed but only one key exists, raises."""
    config = {
        "model": {"name": "gpt-4o-mini"},
        "prompts": {
            "prompt_a": {"name": "A", "system": "Sys A.", "model": "claude-3-opus-20240229"},
            "prompt_b": {"name": "B", "system": "Sys B."},
        },
    }
    # ANTHROPIC_API_KEY present but OPENAI_API_KEY missing
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True):
        with pytest.raises(click.ClickException) as exc_info:
            require_api_key(config)

    assert "OPENAI_API_KEY" in str(exc_info.value.format_message())
