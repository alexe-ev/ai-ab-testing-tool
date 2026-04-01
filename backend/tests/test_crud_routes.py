"""Tests for CRUD API endpoints."""

from src.api.app import app


# ─── Test Sets ────────────────────────────────────────────────────

def test_create_test_set(client):
    payload = {
        "name": "Support Tests",
        "cases": [
            {"case_identifier": "billing-001", "category": "billing", "input": "I was charged twice."},
            {"case_identifier": "tech-001", "category": "technical", "input": "PDF export broken."},
        ],
    }
    resp = client.post("/api/test-sets/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "Support Tests"
    assert len(data["cases"]) == 2


def test_list_test_sets(client):
    client.post("/api/test-sets/", json={"name": "Set A", "cases": [{"case_identifier": "a1", "input": "q1"}]})
    client.post("/api/test-sets/", json={"name": "Set B", "cases": []})
    resp = client.get("/api/test-sets/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Set A" in names
    assert "Set B" in names


def test_get_test_set_by_id(client):
    create_resp = client.post(
        "/api/test-sets/",
        json={
            "name": "My Set",
            "cases": [{"case_identifier": "c1", "category": "cat", "input": "some input"}],
        },
    )
    ts_id = create_resp.json()["id"]
    resp = client.get(f"/api/test-sets/{ts_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == ts_id
    assert len(data["cases"]) == 1
    assert data["cases"][0]["case_identifier"] == "c1"


def test_update_test_set(client):
    create_resp = client.post(
        "/api/test-sets/",
        json={
            "name": "Original",
            "cases": [
                {"case_identifier": "old-001", "input": "old"},
                {"case_identifier": "old-002", "input": "old2"},
            ],
        },
    )
    ts_id = create_resp.json()["id"]
    update_payload = {
        "name": "Updated",
        "cases": [{"case_identifier": "new-001", "input": "new input"}],
    }
    resp = client.put(f"/api/test-sets/{ts_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert len(data["cases"]) == 1
    assert data["cases"][0]["case_identifier"] == "new-001"


def test_delete_test_set(client):
    create_resp = client.post("/api/test-sets/", json={"name": "To Delete", "cases": []})
    ts_id = create_resp.json()["id"]
    resp = client.delete(f"/api/test-sets/{ts_id}")
    assert resp.status_code == 204
    get_resp = client.get(f"/api/test-sets/{ts_id}")
    assert get_resp.status_code == 404


def test_get_test_set_not_found(client):
    resp = client.get("/api/test-sets/nonexistent")
    assert resp.status_code == 404


# ─── Rubrics ──────────────────────────────────────────────────────

def test_create_rubric(client):
    payload = {
        "name": "Support Rubric",
        "dimensions": [
            {
                "name": "accuracy",
                "description": "Is it accurate?",
                "weight": 0.5,
                "levels": [{"score": 5, "description": "perfect"}, {"score": 1, "description": "wrong"}],
            }
        ],
    }
    resp = client.post("/api/rubrics/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "Support Rubric"
    assert len(data["dimensions"]) == 1


def test_list_rubrics(client):
    client.post("/api/rubrics/", json={"name": "Rubric A", "dimensions": []})
    client.post("/api/rubrics/", json={"name": "Rubric B", "dimensions": []})
    resp = client.get("/api/rubrics/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_get_rubric_by_id(client):
    create_resp = client.post(
        "/api/rubrics/",
        json={"name": "My Rubric", "dimensions": [{"name": "dim1", "weight": 1.0, "levels": []}]},
    )
    rubric_id = create_resp.json()["id"]
    resp = client.get(f"/api/rubrics/{rubric_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == rubric_id
    assert len(data["dimensions"]) == 1


def test_update_rubric(client):
    create_resp = client.post(
        "/api/rubrics/",
        json={"name": "Original", "dimensions": [{"name": "d1", "weight": 0.5, "levels": []}]},
    )
    rubric_id = create_resp.json()["id"]
    update_payload = {
        "name": "Updated Rubric",
        "dimensions": [{"name": "d_new", "weight": 1.0, "levels": [{"score": 3, "description": "ok"}]}],
    }
    resp = client.put(f"/api/rubrics/{rubric_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Rubric"
    assert len(data["dimensions"]) == 1
    assert data["dimensions"][0]["name"] == "d_new"


def test_delete_rubric(client):
    create_resp = client.post("/api/rubrics/", json={"name": "To Delete", "dimensions": []})
    rubric_id = create_resp.json()["id"]
    resp = client.delete(f"/api/rubrics/{rubric_id}")
    assert resp.status_code == 204
    get_resp = client.get(f"/api/rubrics/{rubric_id}")
    assert get_resp.status_code == 404


def test_get_rubric_not_found(client):
    resp = client.get("/api/rubrics/nonexistent")
    assert resp.status_code == 404


# ─── Experiments DB ───────────────────────────────────────────────

def test_create_experiment_db(client):
    payload = {"name": "Exp A", "description": "test desc", "hypothesis": "B is better"}
    resp = client.post("/api/experiments-db/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["name"] == "Exp A"
    assert data["description"] == "test desc"
    assert data["hypothesis"] == "B is better"


def test_list_experiments_db(client):
    client.post("/api/experiments-db/", json={"name": "Exp 1"})
    client.post("/api/experiments-db/", json={"name": "Exp 2"})
    resp = client.get("/api/experiments-db/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {item["name"] for item in data}
    assert "Exp 1" in names
    assert "Exp 2" in names


def test_get_experiment_db_by_id(client):
    create_resp = client.post("/api/experiments-db/", json={"name": "My Exp"})
    exp_id = create_resp.json()["id"]
    resp = client.get(f"/api/experiments-db/{exp_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == exp_id
    assert data["name"] == "My Exp"


def test_get_experiment_db_not_found(client):
    resp = client.get("/api/experiments-db/nonexistent")
    assert resp.status_code == 404


def test_update_experiment_db(client):
    create_resp = client.post(
        "/api/experiments-db/",
        json={"name": "Original", "description": "old desc", "hypothesis": "old hyp"},
    )
    exp_id = create_resp.json()["id"]
    update_payload = {"name": "Updated", "description": "new desc", "hypothesis": "new hyp"}
    resp = client.put(f"/api/experiments-db/{exp_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["description"] == "new desc"
    assert data["hypothesis"] == "new hyp"


def test_update_experiment_db_not_found(client):
    resp = client.put("/api/experiments-db/nonexistent", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_experiment_db(client):
    create_resp = client.post("/api/experiments-db/", json={"name": "To Delete"})
    exp_id = create_resp.json()["id"]
    resp = client.delete(f"/api/experiments-db/{exp_id}")
    assert resp.status_code == 204
    get_resp = client.get(f"/api/experiments-db/{exp_id}")
    assert get_resp.status_code == 404


def test_delete_experiment_db_not_found(client):
    resp = client.delete("/api/experiments-db/nonexistent")
    assert resp.status_code == 404


# ─── Invalid data ─────────────────────────────────────────────────

def test_create_test_set_missing_required_field(client):
    # Missing "name"
    resp = client.post("/api/test-sets/", json={"cases": []})
    assert resp.status_code == 422


def test_create_rubric_missing_required_field(client):
    # Missing "name"
    resp = client.post("/api/rubrics/", json={"dimensions": []})
    assert resp.status_code == 422


def test_create_experiment_missing_required_field(client):
    # Missing "name"
    resp = client.post("/api/experiments-db/", json={"description": "no name"})
    assert resp.status_code == 422


# ─── Experiment config field ───────────────────────────────────────

def test_create_experiment_with_config(client):
    config = {
        "prompts": {
            "a": {"name": "Prompt A", "system": "You are helpful.", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 512},
            "b": {"name": "Prompt B", "system": "You are concise.", "model": "claude-haiku", "temperature": 0.3, "max_tokens": 256},
        },
        "judge_model": "claude-sonnet",
    }
    payload = {"name": "Config Exp", "description": "desc", "hypothesis": "hyp", "config": config}
    resp = client.post("/api/experiments-db/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["config"] == config


def test_create_experiment_without_config_returns_null(client):
    resp = client.post("/api/experiments-db/", json={"name": "No Config"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["config"] is None


def test_get_experiment_returns_config(client):
    config = {"judge_model": "gpt-4o", "prompts": {"a": {"name": "A", "system": "sys a", "model": "gpt-4o", "temperature": 0.5, "max_tokens": 100}}}
    create_resp = client.post("/api/experiments-db/", json={"name": "Exp With Config", "config": config})
    exp_id = create_resp.json()["id"]
    resp = client.get(f"/api/experiments-db/{exp_id}")
    assert resp.status_code == 200
    assert resp.json()["config"] == config


def test_update_experiment_config(client):
    create_resp = client.post("/api/experiments-db/", json={"name": "Before Update"})
    exp_id = create_resp.json()["id"]
    new_config = {"judge_model": "claude-sonnet", "prompts": {"a": {"name": "A", "system": "sys", "model": "gpt-4o", "temperature": 0.0, "max_tokens": 50}}}
    resp = client.put(f"/api/experiments-db/{exp_id}", json={"name": "After Update", "config": new_config})
    assert resp.status_code == 200
    assert resp.json()["config"] == new_config


def test_update_experiment_clears_config(client):
    config = {"judge_model": "gpt-4o"}
    create_resp = client.post("/api/experiments-db/", json={"name": "Has Config", "config": config})
    exp_id = create_resp.json()["id"]
    resp = client.put(f"/api/experiments-db/{exp_id}", json={"name": "Has Config", "config": None})
    assert resp.status_code == 200
    assert resp.json()["config"] is None


# ─── Dry-run and run-full endpoints ───────────────────────────────

def _make_experiment_with_config(client):
    config = {
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "a": {"name": "Prompt A", "system": "You are helpful.", "model": "gpt-4o-mini"},
            "b": {"name": "Prompt B", "system": "You are concise.", "model": "gpt-4o-mini"},
        },
        "judge_model": "claude-sonnet",
    }
    resp = client.post("/api/experiments-db/", json={"name": "Run Exp", "config": config})
    return resp.json()["id"]


def _make_test_set(client):
    resp = client.post(
        "/api/test-sets/",
        json={
            "name": "Run Test Set",
            "cases": [
                {"case_identifier": "c1", "category": "billing", "input": "Question 1"},
                {"case_identifier": "c2", "category": "support", "input": "Question 2"},
            ],
        },
    )
    return resp.json()["id"]


def _make_rubric(client):
    resp = client.post(
        "/api/rubrics/",
        json={
            "name": "Run Rubric",
            "dimensions": [
                {
                    "name": "accuracy",
                    "description": "Is it accurate?",
                    "weight": 1.0,
                    "levels": [{"score": 5, "description": "perfect"}, {"score": 1, "description": "wrong"}],
                }
            ],
        },
    )
    return resp.json()["id"]


def test_dry_run_happy_path(client):
    exp_id = _make_experiment_with_config(client)
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)

    resp = client.post(
        f"/api/experiments-db/{exp_id}/dry-run",
        json={"test_set_id": ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["experiment_name"] == "Run Exp"
    assert data["test_case_count"] == 2
    assert set(data["prompt_names"]) == {"a", "b"}
    assert data["rubric_name"] == "Run Rubric"


def test_dry_run_experiment_not_found(client):
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        "/api/experiments-db/nonexistent/dry-run",
        json={"test_set_id": ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 404


def test_dry_run_test_set_not_found(client):
    exp_id = _make_experiment_with_config(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/dry-run",
        json={"test_set_id": "nonexistent", "rubric_id": rubric_id},
    )
    assert resp.status_code == 404


def test_dry_run_rubric_not_found(client):
    exp_id = _make_experiment_with_config(client)
    ts_id = _make_test_set(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/dry-run",
        json={"test_set_id": ts_id, "rubric_id": "nonexistent"},
    )
    assert resp.status_code == 404


def test_dry_run_experiment_no_prompts(client):
    # Experiment with no config -> no prompts
    create_resp = client.post("/api/experiments-db/", json={"name": "No Prompts"})
    exp_id = create_resp.json()["id"]
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/dry-run",
        json={"test_set_id": ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 422


def test_dry_run_experiment_only_one_prompt(client):
    config = {
        "prompts": {
            "a": {"name": "Only A", "system": "sys", "model": "gpt-4o-mini"},
        }
    }
    create_resp = client.post("/api/experiments-db/", json={"name": "One Prompt", "config": config})
    exp_id = create_resp.json()["id"]
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/dry-run",
        json={"test_set_id": ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 422


def test_run_full_returns_job_id(client):
    exp_id = _make_experiment_with_config(client)
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)

    resp = client.post(
        f"/api/experiments-db/{exp_id}/run-full",
        json={
            "test_set_id": ts_id,
            "rubric_id": rubric_id,
            "judge_model": "claude-sonnet-4-20250514",
            "mode": "both",
        },
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert len(data["job_id"]) > 0


def test_run_full_experiment_not_found(client):
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        "/api/experiments-db/nonexistent/run-full",
        json={"test_set_id": ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 404


def test_run_full_test_set_not_found(client):
    exp_id = _make_experiment_with_config(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/run-full",
        json={"test_set_id": "nonexistent", "rubric_id": rubric_id},
    )
    assert resp.status_code == 404


def test_run_full_rubric_not_found(client):
    exp_id = _make_experiment_with_config(client)
    ts_id = _make_test_set(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/run-full",
        json={"test_set_id": ts_id, "rubric_id": "nonexistent"},
    )
    assert resp.status_code == 404


def test_run_full_no_prompts_returns_422(client):
    create_resp = client.post("/api/experiments-db/", json={"name": "No Prompts"})
    exp_id = create_resp.json()["id"]
    ts_id = _make_test_set(client)
    rubric_id = _make_rubric(client)
    resp = client.post(
        f"/api/experiments-db/{exp_id}/run-full",
        json={"test_set_id": ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 422


def test_run_full_empty_test_set_returns_422(client):
    exp_id = _make_experiment_with_config(client)
    rubric_id = _make_rubric(client)
    # Create empty test set
    empty_ts_resp = client.post("/api/test-sets/", json={"name": "Empty Set", "cases": []})
    empty_ts_id = empty_ts_resp.json()["id"]
    resp = client.post(
        f"/api/experiments-db/{exp_id}/run-full",
        json={"test_set_id": empty_ts_id, "rubric_id": rubric_id},
    )
    assert resp.status_code == 422


# ─── Runs endpoints ────────────────────────────────────────────────

def _seed_run(client, exp_id: str, run_id: str) -> None:
    """Seed a Run record directly into the test DB via the app's overridden dependency."""
    from src.api.app import app
    from src.db.engine import get_db

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


# ─── List runs ────────────────────────────────────────────────────

def test_list_runs_happy_path(client):
    exp_id = client.post("/api/experiments-db/", json={"name": "Exp for runs"}).json()["id"]
    _seed_run(client, exp_id, "run-aaa-001")
    _seed_run(client, exp_id, "run-aaa-002")
    resp = client.get(f"/api/experiments-db/{exp_id}/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    run_ids = {r["id"] for r in data}
    assert "run-aaa-001" in run_ids
    assert "run-aaa-002" in run_ids


def test_list_runs_experiment_not_found(client):
    resp = client.get("/api/experiments-db/nonexistent/runs")
    assert resp.status_code == 404


def test_list_runs_empty(client):
    exp_id = client.post("/api/experiments-db/", json={"name": "Empty Exp"}).json()["id"]
    resp = client.get(f"/api/experiments-db/{exp_id}/runs")
    assert resp.status_code == 200
    assert resp.json() == []


# ─── Get run results ──────────────────────────────────────────────

def test_get_run_results_happy_path(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    exp_id = client.post("/api/experiments-db/", json={"name": "Results Exp"}).json()["id"]
    run_id = "results-run-001"
    _seed_run(client, exp_id, run_id)

    import json as _json
    (results_dir / f"run_{run_id}.json").write_text(_json.dumps({"summary": {"total_cases": 2}}))
    (results_dir / f"eval_{run_id}.json").write_text(_json.dumps({"scores": []}))
    (results_dir / f"analysis_{run_id}.json").write_text(_json.dumps({"recommendation": {}}))

    resp = client.get(f"/api/runs/{run_id}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["run_data"] is not None
    assert data["eval_data"] is not None
    assert data["analysis"] is not None


def test_get_run_results_no_files(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()

    exp_id = client.post("/api/experiments-db/", json={"name": "Results Exp 2"}).json()["id"]
    run_id = "results-run-002"
    _seed_run(client, exp_id, run_id)

    resp = client.get(f"/api/runs/{run_id}/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == run_id
    assert data["run_data"] is None
    assert data["eval_data"] is None
    assert data["analysis"] is None


def test_get_run_results_not_found(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    resp = client.get("/api/runs/nonexistent-run/results")
    assert resp.status_code == 404


# ─── Export run ───────────────────────────────────────────────────

def test_export_run_json_happy_path(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    exp_id = client.post("/api/experiments-db/", json={"name": "Export Exp"}).json()["id"]
    run_id = "export-run-001"
    _seed_run(client, exp_id, run_id)

    import json as _json
    (results_dir / f"summary_{run_id}.json").write_text(_json.dumps({"winner": "a"}))

    resp = client.get(f"/api/runs/{run_id}/export/json")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")


def test_export_run_html_happy_path(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    exp_id = client.post("/api/experiments-db/", json={"name": "Export Exp HTML"}).json()["id"]
    run_id = "export-run-html-001"
    _seed_run(client, exp_id, run_id)

    (results_dir / f"report_{run_id}.html").write_text("<html><body>report</body></html>")

    resp = client.get(f"/api/runs/{run_id}/export/html")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")


def test_export_run_not_found(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()
    resp = client.get("/api/runs/nonexistent-run/export/json")
    assert resp.status_code == 404


def test_export_run_invalid_format(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "results").mkdir()

    exp_id = client.post("/api/experiments-db/", json={"name": "Export Inv"}).json()["id"]
    run_id = "export-run-inv-001"
    _seed_run(client, exp_id, run_id)

    resp = client.get(f"/api/runs/{run_id}/export/pdf")
    assert resp.status_code == 422


def test_export_run_file_missing(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    exp_id = client.post("/api/experiments-db/", json={"name": "Export Missing"}).json()["id"]
    run_id = "export-run-miss-001"
    _seed_run(client, exp_id, run_id)

    # No report file created
    resp = client.get(f"/api/runs/{run_id}/export/html")
    assert resp.status_code == 404


# ─── Settings ────────────────────────────────────────────────────

def test_get_settings_returns_all_keys(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    resp = client.get("/api/settings/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    keys = {s["key"] for s in data}
    assert keys == {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
    assert all(not s["is_set"] for s in data)


def test_update_setting(client):
    resp = client.put("/api/settings/", json={"key": "OPENAI_API_KEY", "value": "sk-test-1234567890abcdef"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "OPENAI_API_KEY"
    assert data["is_set"] is True
    assert "****" in data["value"]
    assert data["value"].startswith("sk-t")
    assert data["value"].endswith("cdef")


def test_update_setting_unknown_key(client):
    resp = client.put("/api/settings/", json={"key": "UNKNOWN_KEY", "value": "test"})
    assert resp.status_code == 422


def test_update_setting_empty_value(client):
    resp = client.put("/api/settings/", json={"key": "OPENAI_API_KEY", "value": "  "})
    assert resp.status_code == 422


def test_settings_roundtrip(client):
    client.put("/api/settings/", json={"key": "ANTHROPIC_API_KEY", "value": "sk-ant-test-key-12345"})
    resp = client.get("/api/settings/")
    data = resp.json()
    ant = next(s for s in data if s["key"] == "ANTHROPIC_API_KEY")
    assert ant["is_set"] is True


def test_delete_setting(client):
    client.put("/api/settings/", json={"key": "OPENAI_API_KEY", "value": "sk-test-key"})
    resp = client.delete("/api/settings/OPENAI_API_KEY")
    assert resp.status_code == 204
    data = client.get("/api/settings/").json()
    oai = next(s for s in data if s["key"] == "OPENAI_API_KEY")
    assert oai["is_set"] is False


def test_delete_setting_unknown_key(client):
    resp = client.delete("/api/settings/UNKNOWN")
    assert resp.status_code == 422
