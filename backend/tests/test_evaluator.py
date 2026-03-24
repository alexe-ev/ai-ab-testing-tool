"""Tests for evaluator.py: context injection in evaluation prompts."""

import json
from unittest.mock import patch, MagicMock

import pytest

from src.evaluator import (
    _context_block,
    evaluate_pointwise,
    evaluate_pairwise,
    evaluate_pairwise_with_swap,
)


def _mock_llm_json(data: dict):
    """Return a call_llm side_effect that yields JSON-encoded data."""
    return {
        "response": json.dumps(data),
        "input_tokens": 5,
        "output_tokens": 20,
        "latency_seconds": 0.1,
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
    }


# ─── _context_block ───────────────────────────────────────────────


def test_context_block_none_returns_empty_string():
    assert _context_block(None) == ""


def test_context_block_empty_string_returns_empty():
    # Empty string is falsy, should return ""
    assert _context_block("") == ""


def test_context_block_with_text_includes_context():
    result = _context_block("some context text")
    assert "some context text" in result


def test_context_block_with_text_includes_instruction():
    result = _context_block("some context")
    assert "RETRIEVED CONTEXT" in result
    assert "Evaluate how well the AI used this context" in result


# ─── evaluate_pointwise ───────────────────────────────────────────


def test_evaluate_pointwise_passes_context_to_prompt(sample_rubric):
    """When context is provided, the context block appears in the judge prompt."""
    pointwise_response = {
        "accuracy": {"score": 4, "reasoning": "Good."},
        "clarity": {"score": 3, "reasoning": "Average."},
    }
    client = MagicMock()
    captured_inputs = []

    def capture(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _mock_llm_json(pointwise_response)

    with patch("src.evaluator.call_llm", side_effect=capture):
        evaluate_pointwise(
            client=client,
            case_input="What is the refund policy?",
            response="We offer a 30-day refund.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
            context="User purchased 2 days ago.",
        )

    assert len(captured_inputs) == 1
    assert "User purchased 2 days ago." in captured_inputs[0]
    assert "RETRIEVED CONTEXT" in captured_inputs[0]


def test_evaluate_pointwise_no_context_omits_context_block(sample_rubric):
    """When context is None, no context block appears in the judge prompt."""
    pointwise_response = {
        "accuracy": {"score": 4, "reasoning": "Good."},
        "clarity": {"score": 3, "reasoning": "Average."},
    }
    client = MagicMock()
    captured_inputs = []

    def capture(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _mock_llm_json(pointwise_response)

    with patch("src.evaluator.call_llm", side_effect=capture):
        evaluate_pointwise(
            client=client,
            case_input="What is the refund policy?",
            response="We offer a 30-day refund.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
            context=None,
        )

    assert "RETRIEVED CONTEXT" not in captured_inputs[0]


def test_evaluate_pointwise_returns_scores_for_dimensions(sample_rubric):
    """evaluate_pointwise returns a dict with scores for each dimension."""
    pointwise_response = {
        "accuracy": {"score": 4, "reasoning": "Good."},
        "clarity": {"score": 5, "reasoning": "Excellent."},
    }

    with patch("src.evaluator.call_llm", return_value=_mock_llm_json(pointwise_response)):
        result = evaluate_pointwise(
            client=MagicMock(),
            case_input="Question?",
            response="Answer.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
        )

    assert result["accuracy"]["score"] == 4
    assert result["clarity"]["score"] == 5


# ─── evaluate_pairwise ────────────────────────────────────────────


def test_evaluate_pairwise_passes_context_to_prompt(sample_rubric):
    """When context is provided, it appears in the pairwise judge prompt."""
    pairwise_response = {
        "winner": "A",
        "reasoning": "A was better.",
        "dimension_advantages": {"accuracy": "A", "clarity": "tie"},
    }
    client = MagicMock()
    captured_inputs = []

    def capture(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _mock_llm_json(pairwise_response)

    with patch("src.evaluator.call_llm", side_effect=capture):
        evaluate_pairwise(
            client=client,
            case_input="How do I export?",
            response_a="Click Export then PDF.",
            response_b="Go to settings.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
            context="User is on Pro plan.",
        )

    assert len(captured_inputs) == 1
    assert "User is on Pro plan." in captured_inputs[0]
    assert "RETRIEVED CONTEXT" in captured_inputs[0]


def test_evaluate_pairwise_no_context_omits_context_block(sample_rubric):
    pairwise_response = {
        "winner": "B",
        "reasoning": "B was better.",
        "dimension_advantages": {"accuracy": "B", "clarity": "tie"},
    }

    captured_inputs = []

    def capture(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _mock_llm_json(pairwise_response)

    with patch("src.evaluator.call_llm", side_effect=capture):
        evaluate_pairwise(
            client=MagicMock(),
            case_input="Question?",
            response_a="A answer.",
            response_b="B answer.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
            context=None,
        )

    assert "RETRIEVED CONTEXT" not in captured_inputs[0]


def test_evaluate_pairwise_returns_winner(sample_rubric):
    pairwise_response = {
        "winner": "A",
        "reasoning": "A was better.",
        "dimension_advantages": {"accuracy": "A", "clarity": "tie"},
    }

    with patch("src.evaluator.call_llm", return_value=_mock_llm_json(pairwise_response)):
        result = evaluate_pairwise(
            client=MagicMock(),
            case_input="Question?",
            response_a="A answer.",
            response_b="B answer.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
        )

    assert result["winner"] == "A"


# ─── evaluate_pairwise_with_swap ──────────────────────────────────


def test_evaluate_pairwise_with_swap_passes_context_both_rounds(sample_rubric):
    """Context is passed to both round1 and round2 (swapped order) calls."""
    pairwise_response = {
        "winner": "A",
        "reasoning": "A was better.",
        "dimension_advantages": {"accuracy": "A", "clarity": "A"},
    }
    captured_inputs = []

    def capture(**kwargs):
        captured_inputs.append(kwargs["user_input"])
        return _mock_llm_json(pairwise_response)

    with patch("src.evaluator.call_llm", side_effect=capture):
        evaluate_pairwise_with_swap(
            client=MagicMock(),
            case_input="How do I cancel?",
            response_a="Click Cancel Subscription.",
            response_b="Go to account settings.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
            context="User is on annual plan.",
        )

    assert len(captured_inputs) == 2
    for prompt_text in captured_inputs:
        assert "User is on annual plan." in prompt_text
        assert "RETRIEVED CONTEXT" in prompt_text


def test_evaluate_pairwise_with_swap_consistent_result(sample_rubric):
    """When both rounds agree (A wins round1, B wins round2 swapped = A), result is consistent."""
    responses = [
        # round1: A vs B → A wins
        {
            "winner": "A",
            "reasoning": "A better.",
            "dimension_advantages": {"accuracy": "A", "clarity": "A"},
        },
        # round2 swapped: B vs A → A wins (but in swapped order, A=original B, B=original A)
        # so original winner is B from round2 perspective = A original
        {
            "winner": "B",
            "reasoning": "B better.",
            "dimension_advantages": {"accuracy": "B", "clarity": "B"},
        },
    ]
    call_count = 0

    def side_effect(**kwargs):
        nonlocal call_count
        result = _mock_llm_json(responses[call_count])
        call_count += 1
        return result

    with patch("src.evaluator.call_llm", side_effect=side_effect):
        result = evaluate_pairwise_with_swap(
            client=MagicMock(),
            case_input="Question?",
            response_a="A answer.",
            response_b="B answer.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
        )

    # round1: A wins; round2 (B vs A): B wins → original = A → consistent
    assert result["consistent"] is True
    assert result["winner"] == "A"


def test_evaluate_pairwise_with_swap_inconsistent_result(sample_rubric):
    """When rounds disagree, result is UNCERTAIN and consistent=False."""
    responses = [
        # round1: A vs B → A wins
        {
            "winner": "A",
            "reasoning": "A better.",
            "dimension_advantages": {"accuracy": "A", "clarity": "A"},
        },
        # round2 swapped: B vs A → B wins → original = A (same), but let's make it inconsistent
        # round2 returns A as winner, which in original terms means B won
        {
            "winner": "A",
            "reasoning": "A better.",
            "dimension_advantages": {"accuracy": "A", "clarity": "A"},
        },
    ]
    call_count = 0

    def side_effect(**kwargs):
        nonlocal call_count
        result = _mock_llm_json(responses[call_count])
        call_count += 1
        return result

    with patch("src.evaluator.call_llm", side_effect=side_effect):
        result = evaluate_pairwise_with_swap(
            client=MagicMock(),
            case_input="Question?",
            response_a="A answer.",
            response_b="B answer.",
            rubric=sample_rubric,
            judge_model="claude-sonnet-4-20250514",
            provider="anthropic",
        )

    # round1: A wins; round2 (B vs A): A wins → original = B → inconsistent
    assert result["consistent"] is False
    assert result["winner"] == "UNCERTAIN"
