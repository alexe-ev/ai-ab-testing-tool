"""Tests for pricing.py: calculate_cost() function."""

import pytest

from src.pricing import calculate_cost


def test_calculate_cost_known_model():
    """gpt-4o returns correct USD value."""
    # 1000 input tokens at $2.50/1M = $0.0025
    # 500 output tokens at $10.00/1M = $0.005
    cost = calculate_cost("gpt-4o", 1000, 500)
    assert cost is not None
    assert abs(cost - 0.0075) < 1e-6


def test_calculate_cost_unknown_model():
    """Returns None for unknown model."""
    cost = calculate_cost("unknown-model-xyz", 100, 100)
    assert cost is None


def test_calculate_cost_prefix_matching():
    """claude-sonnet-4-20250514 matches claude-sonnet prefix."""
    cost = calculate_cost("claude-sonnet-4-20250514", 1_000_000, 0)
    assert cost is not None
    # 1M input tokens at $3.00/1M = $3.00
    assert abs(cost - 3.00) < 1e-4


def test_calculate_cost_gpt4o_mini():
    """gpt-4o-mini matches correctly and not gpt-4o."""
    # gpt-4o-mini: $0.15 input, $0.60 output per 1M
    cost = calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost is not None
    expected = 0.15 + 0.60
    assert abs(cost - expected) < 1e-4


def test_calculate_cost_gpt4o_vs_mini_different():
    """gpt-4o and gpt-4o-mini give different costs (longer prefix wins)."""
    cost_mini = calculate_cost("gpt-4o-mini", 1_000_000, 0)
    cost_full = calculate_cost("gpt-4o", 1_000_000, 0)
    assert cost_mini is not None
    assert cost_full is not None
    assert cost_mini != cost_full
    # gpt-4o-mini is cheaper
    assert cost_mini < cost_full


def test_calculate_cost_zero_tokens():
    """Zero tokens gives zero cost."""
    cost = calculate_cost("gpt-4o", 0, 0)
    assert cost == 0.0


def test_calculate_cost_claude_haiku():
    """claude-haiku prefix matching works."""
    cost = calculate_cost("claude-haiku-3-20240307", 1_000_000, 0)
    assert cost is not None
    assert abs(cost - 0.80) < 1e-4


def test_calculate_cost_returns_float():
    """Returns a float (or None)."""
    cost = calculate_cost("gpt-4o", 500, 500)
    assert isinstance(cost, float)
