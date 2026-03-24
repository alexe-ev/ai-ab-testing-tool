"""Tests for llm.detect_provider()."""

from src.llm import detect_provider


def test_claude_prefix_returns_anthropic():
    assert detect_provider("claude-3-5-sonnet-20241022") == "anthropic"


def test_claude_sonnet_returns_anthropic():
    assert detect_provider("claude-sonnet-4-20250514") == "anthropic"


def test_claude3_prefix_returns_anthropic():
    assert detect_provider("claude3-opus") == "anthropic"


def test_gpt_prefix_returns_openai():
    assert detect_provider("gpt-4o-mini") == "openai"


def test_gpt4_returns_openai():
    assert detect_provider("gpt-4") == "openai"


def test_o1_prefix_returns_openai():
    assert detect_provider("o1-preview") == "openai"


def test_o3_prefix_returns_openai():
    assert detect_provider("o3-mini") == "openai"


def test_o4_prefix_returns_openai():
    assert detect_provider("o4-mini") == "openai"


def test_explicit_provider_override_anthropic():
    assert detect_provider("gpt-4o-mini", explicit="anthropic") == "anthropic"


def test_explicit_provider_override_openai():
    assert detect_provider("claude-3-opus", explicit="openai") == "openai"


def test_explicit_provider_lowercased():
    assert detect_provider("gpt-4", explicit="ANTHROPIC") == "anthropic"


def test_unknown_model_defaults_to_openai():
    assert detect_provider("some-unknown-model-xyz") == "openai"


def test_empty_model_defaults_to_openai():
    assert detect_provider("") == "openai"
