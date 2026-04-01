"""Tests for run history: backfill, list endpoint, experiments list, pipeline integration."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.db.engine import Base, get_db
from src.db import crud
from src.api.pipeline_bridge import backfill_summary_metrics, extract_summary_metrics


# ─── Shared DB fixture ────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield engine, TestSession
    app.dependency_overrides.clear()


@pytest.fixture
def db_session(setup_db):
    _, TestSession = setup_db
    db = TestSession()
    yield db
    db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ─── Helpers ──────────────────────────────────────────────────────

def make_experiment(db, name="Test Exp"):
    return crud.create_experiment(db, name=name, description="", hypothesis="")


def make_run(db, run_id, experiment_id=None, status="complete", summary_metrics=None):
    from src.db.models import Run
    run = Run(
        id=run_id,
        experiment_id=experiment_id,
        config={},
        prompt_names={"prompt_a": "Alpha", "prompt_b": "Beta"},
        prompt_models={"prompt_a": "gpt-4o", "prompt_b": "claude-3-opus"},
        total_cases=5,
        error_count=0,
        status=status,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc) if status == "complete" else None,
        summary_metrics=summary_metrics or {},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


SAMPLE_ANALYSIS_DATA = {
    "analysis": {
        "prompt_a": {"key": "prompt_a", "name": "Alpha"},
        "prompt_b": {"key": "prompt_b", "name": "Beta"},
        "pointwise": {
            "overall_weighted": {
                "Alpha": 3.5,
                "Beta": 4.2,
                "better": "Beta",
            }
        },
        "recommendation": {
            "winner": "Beta",
            "confidence": "high",
            "signals": {"for_a": 0, "for_b": 3, "confidence": "high"},
        },
    }
}


# ─── Backfill tests ───────────────────────────────────────────────

def test_backfill_populates_existing_runs(db_session, tmp_path):
    exp = make_experiment(db_session)
    run = make_run(db_session, "run-backfill-001", experiment_id=exp.id, status="complete")

    analysis_file = tmp_path / "analysis_run-backfill-001_timestamp.json"
    analysis_file.write_text(json.dumps(SAMPLE_ANALYSIS_DATA))

    with patch("src.api.pipeline_bridge.Path") as mock_path_cls:
        mock_output_dir = MagicMock()
        mock_output_dir.glob.return_value = [analysis_file]
        mock_path_cls.return_value = mock_output_dir

        backfill_summary_metrics(db_session)

    db_session.refresh(run)
    assert run.summary_metrics.get("winner") == "Beta"
    assert run.summary_metrics.get("confidence") == "high"


def test_backfill_skips_already_populated(db_session, tmp_path):
    exp = make_experiment(db_session)
    existing_metrics = {
        "winner": "Alpha",
        "confidence": "high",
        "score_a": 4.9,
        "score_b": 3.0,
        "score_delta": 1.9,
        "recommendation": "Alpha",
    }
    run = make_run(db_session, "run-skip-001", experiment_id=exp.id, status="complete",
                   summary_metrics=existing_metrics)

    analysis_file = tmp_path / "analysis_run-skip-001.json"
    analysis_file.write_text(json.dumps(SAMPLE_ANALYSIS_DATA))

    with patch("src.api.pipeline_bridge.Path") as mock_path_cls:
        mock_output_dir = MagicMock()
        mock_output_dir.glob.return_value = [analysis_file]
        mock_path_cls.return_value = mock_output_dir

        backfill_summary_metrics(db_session)

    db_session.refresh(run)
    # Should remain unchanged
    assert run.summary_metrics["winner"] == "Alpha"
    assert run.summary_metrics["score_a"] == pytest.approx(4.9)


def test_backfill_handles_missing_analysis(db_session, tmp_path):
    exp = make_experiment(db_session)
    run = make_run(db_session, "run-missing-001", experiment_id=exp.id, status="complete")

    with patch("src.api.pipeline_bridge.Path") as mock_path_cls:
        mock_output_dir = MagicMock()
        mock_output_dir.glob.return_value = []  # no files found
        mock_path_cls.return_value = mock_output_dir

        # Should not raise
        backfill_summary_metrics(db_session)

    db_session.refresh(run)
    assert run.summary_metrics == {}


# ─── List runs endpoint tests ─────────────────────────────────────

def test_list_runs_returns_all(client, db_session):
    exp = make_experiment(db_session)
    make_run(db_session, "run-list-001", experiment_id=exp.id)
    make_run(db_session, "run-list-002", experiment_id=exp.id)

    resp = client.get("/api/runs/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    # Check experiment_name is included
    names = {item["experiment_name"] for item in data["items"]}
    assert exp.name in names


def test_list_runs_filter_experiment(client, db_session):
    exp1 = make_experiment(db_session, name="Exp One")
    exp2 = make_experiment(db_session, name="Exp Two")
    make_run(db_session, "run-filt-001", experiment_id=exp1.id)
    make_run(db_session, "run-filt-002", experiment_id=exp2.id)
    make_run(db_session, "run-filt-003", experiment_id=exp1.id)

    resp = client.get(f"/api/runs/?experiment_id={exp1.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["experiment_id"] == exp1.id


def test_list_runs_filter_status(client, db_session):
    exp = make_experiment(db_session)
    make_run(db_session, "run-stat-001", experiment_id=exp.id, status="complete")
    make_run(db_session, "run-stat-002", experiment_id=exp.id, status="failed")
    make_run(db_session, "run-stat-003", experiment_id=exp.id, status="complete")

    resp = client.get("/api/runs/?status=complete")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["status"] == "complete"


def test_list_runs_sort_by_date(client, db_session):
    from datetime import timedelta

    exp = make_experiment(db_session)
    from src.db.models import Run

    now = datetime.now(timezone.utc)
    r1 = Run(
        id="run-date-001",
        experiment_id=exp.id,
        config={}, prompt_names={}, prompt_models={},
        total_cases=2, error_count=0, status="complete",
        created_at=now - timedelta(days=2),
        summary_metrics={},
    )
    r2 = Run(
        id="run-date-002",
        experiment_id=exp.id,
        config={}, prompt_names={}, prompt_models={},
        total_cases=2, error_count=0, status="complete",
        created_at=now - timedelta(days=1),
        summary_metrics={},
    )
    db_session.add_all([r1, r2])
    db_session.commit()

    resp = client.get("/api/runs/?sort_by=created_at&sort_order=desc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items[0]["id"] == "run-date-002"
    assert items[1]["id"] == "run-date-001"


def test_list_runs_sort_by_delta(client, db_session):
    exp = make_experiment(db_session)
    metrics_low = {"winner": "A", "confidence": "low", "score_a": 3.0, "score_b": 3.1,
                   "score_delta": 0.1, "recommendation": "A"}
    metrics_high = {"winner": "B", "confidence": "high", "score_a": 2.0, "score_b": 4.5,
                    "score_delta": 2.5, "recommendation": "B"}
    make_run(db_session, "run-delta-001", experiment_id=exp.id, summary_metrics=metrics_low)
    make_run(db_session, "run-delta-002", experiment_id=exp.id, summary_metrics=metrics_high)

    resp = client.get("/api/runs/?sort_by=score_delta&sort_order=desc")
    assert resp.status_code == 200
    items = resp.json()["items"]
    # Highest delta first
    assert items[0]["id"] == "run-delta-002"
    assert items[1]["id"] == "run-delta-001"


def test_list_runs_pagination(client, db_session):
    exp = make_experiment(db_session)
    for i in range(5):
        make_run(db_session, f"run-page-{i:03d}", experiment_id=exp.id)

    resp = client.get("/api/runs/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2

    resp2 = client.get("/api/runs/?limit=2&offset=4")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 5
    assert len(data2["items"]) == 1


# ─── Experiments list tests ───────────────────────────────────────

def test_experiments_list_includes_last_run(client, db_session):
    exp = make_experiment(db_session, name="Exp With Runs")
    metrics = {
        "winner": "Alpha",
        "confidence": "high",
        "score_a": 4.5,
        "score_b": 3.2,
        "score_delta": 1.3,
        "recommendation": "Alpha",
    }
    make_run(db_session, "run-explist-001", experiment_id=exp.id, status="complete",
             summary_metrics=metrics)

    resp = client.get("/api/experiments-db/")
    assert resp.status_code == 200
    items = resp.json()
    exp_item = next((e for e in items if e["id"] == exp.id), None)
    assert exp_item is not None
    assert exp_item["last_run_metrics"] is not None
    assert exp_item["last_run_metrics"]["winner"] == "Alpha"
    assert exp_item["last_run_at"] is not None


def test_experiments_list_no_runs(client, db_session):
    exp = make_experiment(db_session, name="Exp No Runs")

    resp = client.get("/api/experiments-db/")
    assert resp.status_code == 200
    items = resp.json()
    exp_item = next((e for e in items if e["id"] == exp.id), None)
    assert exp_item is not None
    assert exp_item["last_run_metrics"] is None
    assert exp_item["last_run_at"] is None


# ─── Pipeline integration test ────────────────────────────────────

def test_extract_and_store_summary_metrics(db_session, tmp_path):
    """After analysis step, Run record should have summary_metrics populated."""
    from src.db.models import Run

    exp = make_experiment(db_session)
    run = make_run(db_session, "run-pipe-001", experiment_id=exp.id, status="running",
                   summary_metrics={})

    analysis_file = tmp_path / "analysis_run-pipe-001.json"
    analysis_file.write_text(json.dumps(SAMPLE_ANALYSIS_DATA))

    # Simulate what run_full_pipeline does after analysis step
    from src.api.pipeline_bridge import extract_summary_metrics
    with open(analysis_file) as f:
        analysis_data = json.load(f)
    metrics = extract_summary_metrics(analysis_data)
    assert metrics, "extract_summary_metrics returned empty dict"

    run_record = db_session.query(Run).filter_by(id="run-pipe-001").first()
    run_record.summary_metrics = metrics
    db_session.commit()

    db_session.refresh(run_record)
    assert run_record.summary_metrics["winner"] == "Beta"
    assert run_record.summary_metrics["confidence"] == "high"
    assert run_record.summary_metrics["score_delta"] == pytest.approx(abs(3.5 - 4.2), abs=1e-4)
