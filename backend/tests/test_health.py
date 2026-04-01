"""Tests for the health check endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint_returns_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_endpoint_has_status_field(client):
    resp = client.get("/api/health")
    data = resp.json()
    assert "status" in data
