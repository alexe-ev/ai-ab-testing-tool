"""Tests for clone and iteration chain endpoints."""

from src.api.app import app
from src.db.engine import get_db


SAMPLE_CONFIG = {
    "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
    "prompts": {
        "a": {"name": "Prompt A", "system": "You are helpful."},
        "b": {"name": "Prompt B", "system": "You are concise."},
    },
    "judge_model": "claude-sonnet",
}


def _make_exp(client, name: str, config=None, parent_id=None) -> dict:
    payload = {"name": name}
    if config is not None:
        payload["config"] = config
    if parent_id is not None:
        payload["parent_id"] = parent_id
    resp = client.post("/api/experiments-db/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _seed_run(client, exp_id: str, run_id: str, status: str = "complete") -> None:
    db = next(app.dependency_overrides[get_db]())
    from src.db import crud
    run = crud.create_run(
        db,
        run_id=run_id,
        experiment_id=exp_id,
        config={},
        prompt_names={"a": "Prompt A", "b": "Prompt B"},
        prompt_models={"a": "gpt-4o", "b": "gpt-4o"},
        total_cases=2,
        status=status,
    )
    if status == "complete":
        crud.update_run_status(db, run_id, "complete")
        crud.update_run_summary_metrics(db, run_id, {
            "winner": "a",
            "confidence": "high",
            "score_a": 4.0,
            "score_b": 3.5,
            "score_delta": 0.5,
            "recommendation": "Use A",
        })


# ─── Clone tests ─────────────────────────────────────────────────

def test_clone_experiment_copies_config(client):
    original = _make_exp(client, "Original", config=SAMPLE_CONFIG)
    resp = client.post(f"/api/experiments-db/{original['id']}/clone", json={})
    assert resp.status_code == 201
    cloned = resp.json()
    assert cloned["config"] == SAMPLE_CONFIG


def test_clone_experiment_sets_parent_id(client):
    original = _make_exp(client, "Original", config=SAMPLE_CONFIG)
    resp = client.post(f"/api/experiments-db/{original['id']}/clone", json={})
    assert resp.status_code == 201
    cloned = resp.json()
    assert cloned["parent_id"] == original["id"]


def test_clone_experiment_default_name(client):
    original = _make_exp(client, "My Experiment", config=SAMPLE_CONFIG)
    resp = client.post(f"/api/experiments-db/{original['id']}/clone", json={})
    assert resp.status_code == 201
    cloned = resp.json()
    assert cloned["name"] == "My Experiment v2"


def test_clone_experiment_default_name_increments(client):
    original = _make_exp(client, "My Experiment", config=SAMPLE_CONFIG)
    # clone once
    client.post(f"/api/experiments-db/{original['id']}/clone", json={})
    # clone again
    resp = client.post(f"/api/experiments-db/{original['id']}/clone", json={})
    assert resp.status_code == 201
    cloned = resp.json()
    assert cloned["name"] == "My Experiment v3"


def test_clone_experiment_custom_name(client):
    original = _make_exp(client, "Original", config=SAMPLE_CONFIG)
    resp = client.post(f"/api/experiments-db/{original['id']}/clone", json={"name": "Custom Clone Name"})
    assert resp.status_code == 201
    cloned = resp.json()
    assert cloned["name"] == "Custom Clone Name"


def test_clone_experiment_copies_description_hypothesis(client):
    resp = client.post(
        "/api/experiments-db/",
        json={"name": "Full Exp", "description": "some desc", "hypothesis": "B wins", "config": SAMPLE_CONFIG},
    )
    original = resp.json()
    clone_resp = client.post(f"/api/experiments-db/{original['id']}/clone", json={})
    assert clone_resp.status_code == 201
    cloned = clone_resp.json()
    assert cloned["description"] == "some desc"
    assert cloned["hypothesis"] == "B wins"


def test_clone_experiment_not_found(client):
    resp = client.post("/api/experiments-db/nonexistent/clone", json={})
    assert resp.status_code == 404


# ─── Iteration chain tests ────────────────────────────────────────

def test_iteration_chain_single_experiment(client):
    exp = _make_exp(client, "Standalone")
    resp = client.get(f"/api/experiments-db/{exp['id']}/chain")
    assert resp.status_code == 200
    chain = resp.json()
    assert len(chain) == 1
    assert chain[0]["id"] == exp["id"]


def test_iteration_chain_returns_ordered(client):
    v1 = _make_exp(client, "Exp v1")
    v2_resp = client.post(f"/api/experiments-db/{v1['id']}/clone", json={"name": "Exp v2"})
    v2 = v2_resp.json()
    v3_resp = client.post(f"/api/experiments-db/{v2['id']}/clone", json={"name": "Exp v3"})
    v3 = v3_resp.json()

    resp = client.get(f"/api/experiments-db/{v1['id']}/chain")
    assert resp.status_code == 200
    chain = resp.json()
    assert len(chain) == 3
    ids = [item["id"] for item in chain]
    assert ids.index(v1["id"]) < ids.index(v2["id"]) < ids.index(v3["id"])


def test_iteration_chain_from_child_returns_full_chain(client):
    v1 = _make_exp(client, "Root")
    v2_resp = client.post(f"/api/experiments-db/{v1['id']}/clone", json={"name": "Child"})
    v2 = v2_resp.json()

    # query from child — should still return full chain
    resp = client.get(f"/api/experiments-db/{v2['id']}/chain")
    assert resp.status_code == 200
    chain = resp.json()
    assert len(chain) == 2
    ids = [item["id"] for item in chain]
    assert v1["id"] in ids
    assert v2["id"] in ids


def test_iteration_chain_deep(client):
    root = _make_exp(client, "v1")
    current_id = root["id"]
    for i in range(2, 7):
        resp = client.post(f"/api/experiments-db/{current_id}/clone", json={"name": f"v{i}"})
        current_id = resp.json()["id"]

    resp = client.get(f"/api/experiments-db/{root['id']}/chain")
    assert resp.status_code == 200
    chain = resp.json()
    assert len(chain) == 6


def test_iteration_chain_not_found(client):
    resp = client.get("/api/experiments-db/nonexistent/chain")
    assert resp.status_code == 404


def test_iteration_chain_includes_last_run_metrics(client):
    v1 = _make_exp(client, "With Runs")
    _seed_run(client, v1["id"], "run-chain-001")
    resp = client.get(f"/api/experiments-db/{v1['id']}/chain")
    assert resp.status_code == 200
    chain = resp.json()
    assert chain[0]["last_run_metrics"] is not None
    assert chain[0]["last_run_metrics"]["winner"] == "a"
