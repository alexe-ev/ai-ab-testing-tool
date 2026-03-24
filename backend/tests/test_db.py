"""Tests for database CRUD operations using in-memory SQLite."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.engine import Base
from src.db.models import Experiment, TestSet, TestCase, Rubric, RubricDimension, Run
from src.db import crud


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ─── Test Sets ────────────────────────────────────────────────────

def test_create_test_set_with_cases(db):
    cases = [
        {"case_identifier": "billing-001", "category": "billing", "input": "I was charged twice."},
        {"case_identifier": "tech-001", "category": "technical", "input": "PDF export broken."},
    ]
    ts = crud.create_test_set(db, name="Support Tests", cases=cases)
    assert ts.id is not None
    assert ts.name == "Support Tests"
    assert len(ts.cases) == 2


def test_get_test_set_by_id(db):
    cases = [
        {"case_identifier": "c1", "category": "cat", "input": "some input"},
    ]
    ts = crud.create_test_set(db, name="My Set", cases=cases)
    fetched = crud.get_test_set(db, ts.id)
    assert fetched is not None
    assert fetched.id == ts.id
    assert len(fetched.cases) == 1
    assert fetched.cases[0].case_identifier == "c1"


def test_get_test_set_not_found(db):
    result = crud.get_test_set(db, "nonexistent-id")
    assert result is None


def test_list_test_sets(db):
    crud.create_test_set(db, name="Set A", cases=[{"case_identifier": "a1", "input": "q1"}])
    crud.create_test_set(db, name="Set B", cases=[{"case_identifier": "b1", "input": "q2"}])
    rows = crud.list_test_sets(db)
    assert len(rows) == 2
    names = {ts.name for ts, _ in rows}
    assert "Set A" in names
    assert "Set B" in names


def test_update_test_set_replaces_cases(db):
    original_cases = [
        {"case_identifier": "old-001", "category": "old", "input": "old input"},
        {"case_identifier": "old-002", "category": "old", "input": "old input 2"},
    ]
    ts = crud.create_test_set(db, name="Original", cases=original_cases)
    assert len(ts.cases) == 2

    new_cases = [
        {"case_identifier": "new-001", "category": "new", "input": "new input"},
    ]
    updated = crud.update_test_set(db, id=ts.id, name="Updated", cases=new_cases)
    assert updated is not None
    assert updated.name == "Updated"
    assert len(updated.cases) == 1
    assert updated.cases[0].case_identifier == "new-001"


def test_delete_test_set_cascade(db):
    cases = [
        {"case_identifier": "c1", "input": "input 1"},
        {"case_identifier": "c2", "input": "input 2"},
    ]
    ts = crud.create_test_set(db, name="To Delete", cases=cases)
    ts_id = ts.id
    case_ids = [c.id for c in ts.cases]

    result = crud.delete_test_set(db, ts_id)
    assert result is True

    assert crud.get_test_set(db, ts_id) is None
    for cid in case_ids:
        assert db.query(TestCase).filter(TestCase.id == cid).first() is None


def test_delete_test_set_not_found(db):
    result = crud.delete_test_set(db, "nonexistent")
    assert result is False


# ─── Rubrics ──────────────────────────────────────────────────────

def test_create_rubric_with_dimensions(db):
    dims = [
        {
            "name": "accuracy",
            "description": "Is it accurate?",
            "weight": 0.5,
            "levels": [{"score": 5, "description": "perfect"}, {"score": 1, "description": "wrong"}],
        },
        {
            "name": "empathy",
            "description": "Is it empathetic?",
            "weight": 0.5,
            "levels": [{"score": 5, "description": "warm"}, {"score": 1, "description": "cold"}],
        },
    ]
    rubric = crud.create_rubric(db, name="Support Rubric", dimensions=dims)
    assert rubric.id is not None
    assert rubric.name == "Support Rubric"
    assert len(rubric.dimensions) == 2


def test_get_rubric_by_id(db):
    dims = [{"name": "accuracy", "weight": 1.0, "levels": []}]
    rubric = crud.create_rubric(db, name="Test Rubric", dimensions=dims)
    fetched = crud.get_rubric(db, rubric.id)
    assert fetched is not None
    assert fetched.id == rubric.id
    assert len(fetched.dimensions) == 1
    assert fetched.dimensions[0].name == "accuracy"


def test_get_rubric_not_found(db):
    result = crud.get_rubric(db, "nonexistent")
    assert result is None


def test_list_rubrics(db):
    crud.create_rubric(db, name="Rubric A", dimensions=[])
    crud.create_rubric(db, name="Rubric B", dimensions=[])
    rubrics = crud.list_rubrics(db)
    assert len(rubrics) == 2


def test_update_rubric_replaces_dimensions(db):
    original_dims = [
        {"name": "dim1", "weight": 0.5, "levels": []},
        {"name": "dim2", "weight": 0.5, "levels": []},
    ]
    rubric = crud.create_rubric(db, name="Original", dimensions=original_dims)
    assert len(rubric.dimensions) == 2

    new_dims = [{"name": "dim_new", "weight": 1.0, "levels": [{"score": 3, "description": "ok"}]}]
    updated = crud.update_rubric(db, id=rubric.id, name="Updated Rubric", dimensions=new_dims)
    assert updated is not None
    assert updated.name == "Updated Rubric"
    assert len(updated.dimensions) == 1
    assert updated.dimensions[0].name == "dim_new"


def test_delete_rubric_cascade(db):
    dims = [
        {"name": "dim1", "weight": 1.0, "levels": []},
    ]
    rubric = crud.create_rubric(db, name="To Delete", dimensions=dims)
    rubric_id = rubric.id
    dim_ids = [d.id for d in rubric.dimensions]

    result = crud.delete_rubric(db, rubric_id)
    assert result is True

    assert crud.get_rubric(db, rubric_id) is None
    for did in dim_ids:
        assert db.query(RubricDimension).filter(RubricDimension.id == did).first() is None


def test_delete_rubric_not_found(db):
    result = crud.delete_rubric(db, "nonexistent")
    assert result is False


# ─── Experiments ──────────────────────────────────────────────────

def test_create_experiment(db):
    exp = crud.create_experiment(db, name="Exp A", description="test desc", hypothesis="B is better")
    assert exp.id is not None
    assert exp.name == "Exp A"
    assert exp.description == "test desc"
    assert exp.hypothesis == "B is better"


def test_list_experiments_with_run_count(db):
    exp = crud.create_experiment(db, name="Exp With Runs")
    crud.create_run(
        db,
        run_id="run-001",
        experiment_id=exp.id,
        config={},
        prompt_names={},
        prompt_models={},
        total_cases=5,
    )
    crud.create_run(
        db,
        run_id="run-002",
        experiment_id=exp.id,
        config={},
        prompt_names={},
        prompt_models={},
        total_cases=3,
    )
    rows = crud.list_experiments(db)
    assert len(rows) == 1
    exp_obj, run_count = rows[0]
    assert run_count == 2


def test_update_experiment(db):
    exp = crud.create_experiment(db, name="Original", description="old desc", hypothesis="old hyp")
    updated = crud.update_experiment(db, id=exp.id, name="Updated", description="new desc", hypothesis="new hyp")
    assert updated is not None
    assert updated.name == "Updated"
    assert updated.description == "new desc"
    assert updated.hypothesis == "new hyp"


def test_update_experiment_not_found(db):
    result = crud.update_experiment(db, id="nonexistent", name="X")
    assert result is None


def test_delete_experiment_cascade(db):
    exp = crud.create_experiment(db, name="To Delete")
    run = crud.create_run(
        db,
        run_id="run-cascade",
        experiment_id=exp.id,
        config={},
        prompt_names={},
        prompt_models={},
        total_cases=1,
    )
    exp_id = exp.id
    result = crud.delete_experiment(db, exp_id)
    assert result is True
    assert crud.get_experiment(db, exp_id) is None
    assert db.query(Run).filter(Run.id == run.id).first() is None


def test_delete_experiment_not_found(db):
    result = crud.delete_experiment(db, "nonexistent")
    assert result is False


# ─── Runs ─────────────────────────────────────────────────────────

def test_create_run(db):
    run = crud.create_run(
        db,
        run_id="test-run-123",
        experiment_id=None,
        config={"experiment": {"name": "x"}},
        prompt_names={"prompt_a": "Minimal"},
        prompt_models={"prompt_a": "gpt-4o-mini"},
        total_cases=10,
    )
    assert run.id == "test-run-123"
    assert run.status == "pending"
    assert run.total_cases == 10


def test_update_run_status(db):
    crud.create_run(
        db,
        run_id="run-to-update",
        experiment_id=None,
        config={},
        prompt_names={},
        prompt_models={},
        total_cases=5,
    )
    updated = crud.update_run_status(
        db,
        run_id="run-to-update",
        status="complete",
        result_path="results/run_xyz.json",
        error_count=1,
    )
    assert updated is not None
    assert updated.status == "complete"
    assert updated.result_path == "results/run_xyz.json"
    assert updated.error_count == 1
    assert updated.completed_at is not None


def test_update_run_status_not_found(db):
    result = crud.update_run_status(db, run_id="nonexistent", status="failed")
    assert result is None
