"""Tests for extract_summary_metrics function."""

import pytest
from src.api.pipeline_bridge import extract_summary_metrics


VALID_ANALYSIS = {
    "analysis": {
        "prompt_a": {"key": "prompt_a", "name": "Minimal"},
        "prompt_b": {"key": "prompt_b", "name": "Detailed"},
        "pointwise": {
            "overall_weighted": {
                "Minimal": 3.58,
                "Detailed": 4.66,
                "better": "Detailed",
            }
        },
        "recommendation": {
            "winner": "Detailed",
            "confidence": "medium",
            "signals": {"for_a": 0, "for_b": 2, "confidence": "medium"},
        },
    }
}


def test_extract_summary_metrics_complete():
    metrics = extract_summary_metrics(VALID_ANALYSIS)

    assert metrics["winner"] == "Detailed"
    assert metrics["confidence"] == "medium"
    assert metrics["score_a"] == pytest.approx(3.58, abs=1e-4)
    assert metrics["score_b"] == pytest.approx(4.66, abs=1e-4)
    assert metrics["score_delta"] == pytest.approx(abs(3.58 - 4.66), abs=1e-4)
    assert "recommendation" in metrics


def test_extract_summary_metrics_missing_data():
    # Malformed: missing pointwise
    broken = {
        "analysis": {
            "prompt_a": {"key": "prompt_a", "name": "A"},
            "prompt_b": {"key": "prompt_b", "name": "B"},
            "recommendation": {"winner": "A", "confidence": "low"},
        }
    }
    result = extract_summary_metrics(broken)
    assert result == {}


def test_extract_summary_metrics_tie():
    tie_analysis = {
        "analysis": {
            "prompt_a": {"key": "prompt_a", "name": "Alpha"},
            "prompt_b": {"key": "prompt_b", "name": "Beta"},
            "pointwise": {
                "overall_weighted": {
                    "Alpha": 4.0,
                    "Beta": 4.0,
                    "better": "tie",
                }
            },
            "recommendation": {
                "winner": "tie",
                "confidence": "low",
                "signals": {"for_a": 1, "for_b": 1, "confidence": "low"},
            },
        }
    }
    metrics = extract_summary_metrics(tie_analysis)
    assert metrics["winner"] == "tie"
    assert metrics["score_delta"] == pytest.approx(0.0, abs=1e-4)
    assert metrics["score_a"] == pytest.approx(4.0, abs=1e-4)
    assert metrics["score_b"] == pytest.approx(4.0, abs=1e-4)
