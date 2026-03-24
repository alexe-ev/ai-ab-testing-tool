"""Tests for FastAPI backend endpoints."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.app import app
from src.api import jobs as jobs_module


@pytest.fixture(autouse=True)
def clear_jobs():
    """Clear job store before each test."""
    jobs_module.clear_all()
    yield
    jobs_module.clear_all()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_config_payload():
    return {
        "config": {
            "experiment": {"name": "test-exp"},
            "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
            "prompts": {
                "prompt_a": {"name": "Minimal", "system": "You are helpful."},
                "prompt_b": {"name": "Detailed", "system": "You are very helpful."},
            },
            "test_set": "test_sets/support_5.yaml",
            "rubric": "rubrics/support.yaml",
        }
    }


# ─── Health ───────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ─── Dry run ──────────────────────────────────────────────────────

def test_dry_run_valid_config(client, sample_config_payload):
    mock_cases = [
        {"id": "c1", "category": "billing", "input": "test1"},
        {"id": "c2", "category": "tech", "input": "test2"},
    ]

    with patch("src.api.routes.load_test_set", return_value=mock_cases), \
         patch("src.api.routes.run_experiment", return_value=""):
        resp = client.post("/api/experiments/dry-run", json=sample_config_payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["experiment_name"] == "test-exp"
    assert data["model"] == "gpt-4o-mini"
    assert data["test_case_count"] == 2
    assert data["estimated_calls"] == 4  # 2 cases * 2 prompts
    assert "prompt_a" in data["prompt_names"]
    assert "prompt_b" in data["prompt_names"]


def test_dry_run_invalid_config_missing_fields(client):
    # Missing required fields
    payload = {"config": {"experiment": {"name": "x"}}}
    resp = client.post("/api/experiments/dry-run", json=payload)
    assert resp.status_code == 422


def test_dry_run_invalid_config_schema(client):
    # Not a dict for config
    resp = client.post("/api/experiments/dry-run", json={"config": "not-a-dict"})
    assert resp.status_code == 422


# ─── Run (async) ──────────────────────────────────────────────────

def test_start_run_returns_job_id(client, sample_config_payload):
    with patch("src.api.routes.run_experiment", return_value="results/run_test_20240101_000000_abc123.json"):
        resp = client.post("/api/experiments/run", json=sample_config_payload)

    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert len(data["job_id"]) > 0


def test_start_run_job_is_created(client, sample_config_payload):
    with patch("src.api.routes.run_experiment", return_value="results/run_x.json"):
        resp = client.post("/api/experiments/run", json=sample_config_payload)

    job_id = resp.json()["job_id"]
    job = jobs_module.get_job(job_id)
    assert job is not None
    assert job["status"] in ("pending", "running", "done", "failed")


# ─── Job status ───────────────────────────────────────────────────

def test_job_status_not_found(client):
    resp = client.get("/api/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_job_status_exists(client):
    job_id = jobs_module.create_job()
    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["status"] == "pending"
    assert "created_at" in data
    assert "updated_at" in data


def test_job_status_after_update(client):
    job_id = jobs_module.create_job()
    jobs_module.update_job(job_id, "done", result={"run_id": "abc"})
    resp = client.get(f"/api/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert data["result"] == {"run_id": "abc"}


# ─── Results ──────────────────────────────────────────────────────

def test_results_not_found(client):
    resp = client.get("/api/experiments/nonexistent-run-id/results")
    assert resp.status_code == 404


def test_results_found(client, tmp_path):
    run_id = "mytest_20240101_000000_abc123"
    run_data = {
        "run_id": run_id,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "config": {"experiment": {"name": "x"}, "model": {"name": "gpt-4o-mini"}, "prompt_names": {}, "prompt_models": {}},
        "results": [],
        "summary": {"total_cases": 0, "total_calls": 0, "errors": 0},
    }
    run_file = tmp_path / f"run_{run_id}.json"
    run_file.write_text(json.dumps(run_data))

    with patch("src.api.routes.OUTPUT_DIR", str(tmp_path)):
        resp = client.get(f"/api/experiments/{run_id}/results")

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["run_data"]["run_id"] == run_id
    assert data["eval_data"] is None
    assert data["analysis"] is None


# ─── CORS ─────────────────────────────────────────────────────────

def test_cors_headers(client):
    resp = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


# ─── Analyze with mock data ───────────────────────────────────────

def test_analyze_with_mock_data(client, tmp_path):
    """Create a real eval JSON and run analysis through the endpoint."""
    run_id = "testrun_20240101_000000_abc"

    eval_data = {
        "eval_id": f"eval_{run_id}",
        "run_id": run_id,
        "timestamp": "2024-01-01T00:00:00+00:00",
        "config": {
            "mode": "both",
            "judge_model": "claude-sonnet-4-20250514",
            "rubric_path": "rubrics/test.yaml",
            "prompt_a": {"key": "prompt_a", "name": "Minimal"},
            "prompt_b": {"key": "prompt_b", "name": "Detailed"},
        },
        "rubric": {
            "dimensions": [
                {
                    "name": "accuracy",
                    "weight": 1.0,
                    "levels": [
                        {"score": 5, "description": "Correct"},
                        {"score": 1, "description": "Wrong"},
                    ],
                }
            ]
        },
        "evaluations": [
            {
                "test_case_id": "c1",
                "category": "billing",
                "input": "test",
                "pointwise": {
                    "prompt_a": {"accuracy": {"score": 4, "reasoning": "good"}},
                    "prompt_b": {"accuracy": {"score": 3, "reasoning": "ok"}},
                },
                "pairwise": {
                    "winner": "A",
                    "consistent": True,
                    "round1": {"winner": "A", "reasoning": "A better"},
                    "round2_swapped": {"winner": "B", "reasoning": "A better"},
                    "round2_mapped_winner": "A",
                },
            },
            {
                "test_case_id": "c2",
                "category": "tech",
                "input": "test2",
                "pointwise": {
                    "prompt_a": {"accuracy": {"score": 3, "reasoning": "ok"}},
                    "prompt_b": {"accuracy": {"score": 4, "reasoning": "good"}},
                },
                "pairwise": {
                    "winner": "B",
                    "consistent": True,
                    "round1": {"winner": "B", "reasoning": "B better"},
                    "round2_swapped": {"winner": "A", "reasoning": "B better"},
                    "round2_mapped_winner": "B",
                },
            },
            {
                "test_case_id": "c3",
                "category": "billing",
                "input": "test3",
                "pointwise": {
                    "prompt_a": {"accuracy": {"score": 5, "reasoning": "great"}},
                    "prompt_b": {"accuracy": {"score": 2, "reasoning": "poor"}},
                },
                "pairwise": {
                    "winner": "A",
                    "consistent": True,
                    "round1": {"winner": "A", "reasoning": "A better"},
                    "round2_swapped": {"winner": "B", "reasoning": "A better"},
                    "round2_mapped_winner": "A",
                },
            },
        ],
        "summary": {
            "total_cases": 3,
            "evaluated": 3,
            "skipped": 0,
            "eval_api_calls": 6,
        },
    }

    eval_file = tmp_path / f"eval_{run_id}.json"
    eval_file.write_text(json.dumps(eval_data))

    with patch("src.api.routes.OUTPUT_DIR", str(tmp_path)):
        resp = client.post(f"/api/experiments/{run_id}/analyze")

    assert resp.status_code == 200
    data = resp.json()
    assert "analysis" in data
    assert data["run_id"] == run_id
