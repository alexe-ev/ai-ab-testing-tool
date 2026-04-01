"""Tests for compare endpoint and parent_id experiment support."""

import json

from src.api.app import app
from src.db.engine import get_db


def _seed_run_with_files(client, exp_id: str, run_id: str, tmp_path) -> None:
    db = next(app.dependency_overrides[get_db]())
    from src.db import crud

    crud.create_run(
        db,
        run_id=run_id,
        experiment_id=exp_id,
        config={},
        prompt_names={"a": "Prompt A", "b": "Prompt B"},
        prompt_models={"a": "gpt-4o", "b": "gpt-4o"},
        total_cases=2,
        status="complete",
    )
    crud.update_run_status(db, run_id, "complete")

    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / f"run_{run_id}.json").write_text(json.dumps({"summary": {"total_cases": 2}}))
    (results_dir / f"eval_{run_id}.json").write_text(json.dumps({"scores": []}))
    (results_dir / f"analysis_{run_id}.json").write_text(json.dumps({"recommendation": {"winner": "a"}}))


def _seed_run_no_files(client, exp_id: str, run_id: str) -> None:
    db = next(app.dependency_overrides[get_db]())
    from src.db import crud
    crud.create_run(
        db,
        run_id=run_id,
        experiment_id=exp_id,
        config={},
        prompt_names={"a": "Prompt A", "b": "Prompt B"},
        prompt_models={"a": "gpt-4o", "b": "gpt-4o"},
        total_cases=2,
        status="complete",
    )


# ─── Compare endpoint ─────────────────────────────────────────────

def test_compare_endpoint_returns_both(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    exp_id = client.post("/api/experiments-db/", json={"name": "Cmp Exp"}).json()["id"]
    _seed_run_with_files(client, exp_id, "cmp-run-a", tmp_path)
    _seed_run_with_files(client, exp_id, "cmp-run-b", tmp_path)

    resp = client.get("/api/runs/compare?run_a=cmp-run-a&run_b=cmp-run-b")
    assert resp.status_code == 200
    data = resp.json()
    assert "run_a" in data
    assert "run_b" in data
    assert data["run_a"]["run_id"] == "cmp-run-a"
    assert data["run_b"]["run_id"] == "cmp-run-b"
    assert data["run_a"]["analysis"] is not None
    assert data["run_b"]["analysis"] is not None


def test_compare_endpoint_invalid_run(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    exp_id = client.post("/api/experiments-db/", json={"name": "Cmp Exp 2"}).json()["id"]
    _seed_run_with_files(client, exp_id, "cmp-run-real", tmp_path)

    resp = client.get("/api/runs/compare?run_a=cmp-run-real&run_b=nonexistent-run")
    assert resp.status_code == 404


def test_compare_endpoint_run_no_files(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    exp_id = client.post("/api/experiments-db/", json={"name": "Cmp Exp 3"}).json()["id"]
    _seed_run_no_files(client, exp_id, "cmp-no-files-a")
    _seed_run_no_files(client, exp_id, "cmp-no-files-b")

    resp = client.get("/api/runs/compare?run_a=cmp-no-files-a&run_b=cmp-no-files-b")
    assert resp.status_code == 404


# ─── Experiment create/list with parent_id ────────────────────────

def test_experiment_create_with_parent_id(client):
    parent = client.post("/api/experiments-db/", json={"name": "Parent Exp"}).json()
    resp = client.post(
        "/api/experiments-db/",
        json={"name": "Child Exp", "parent_id": parent["id"]},
    )
    assert resp.status_code == 201
    child = resp.json()
    assert child["parent_id"] == parent["id"]


def test_experiment_list_includes_parent_id(client):
    parent = client.post("/api/experiments-db/", json={"name": "Parent"}).json()
    client.post("/api/experiments-db/", json={"name": "Child", "parent_id": parent["id"]})

    resp = client.get("/api/experiments-db/")
    assert resp.status_code == 200
    items = resp.json()
    child_item = next((x for x in items if x["name"] == "Child"), None)
    assert child_item is not None
    assert child_item["parent_id"] == parent["id"]

    parent_item = next((x for x in items if x["name"] == "Parent"), None)
    assert parent_item is not None
    assert parent_item["parent_id"] is None


def test_delete_parent_nullifies_children(client):
    parent = client.post("/api/experiments-db/", json={"name": "Parent"}).json()
    child_resp = client.post(
        "/api/experiments-db/",
        json={"name": "Child", "parent_id": parent["id"]},
    )
    child_id = child_resp.json()["id"]

    # Delete parent
    del_resp = client.delete(f"/api/experiments-db/{parent['id']}")
    assert del_resp.status_code == 204

    # Child should still exist but parent_id should be nullified (SET NULL)
    child_get = client.get(f"/api/experiments-db/{child_id}")
    assert child_get.status_code == 200
    assert child_get.json()["parent_id"] is None
