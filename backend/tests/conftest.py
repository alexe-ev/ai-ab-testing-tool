"""Shared fixtures for the test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.app import app
from src.db.engine import Base, get_db


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
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_rubric():
    return {
        "dimensions": [
            {
                "name": "accuracy",
                "weight": 0.5,
                "levels": [
                    {"score": 5, "description": "Fully correct."},
                    {"score": 1, "description": "Incorrect."},
                ],
            },
            {
                "name": "clarity",
                "weight": 0.5,
                "levels": [
                    {"score": 5, "description": "Very clear."},
                    {"score": 1, "description": "Unclear."},
                ],
            },
        ]
    }


@pytest.fixture
def sample_test_cases():
    return [
        {
            "id": "case-001",
            "category": "billing",
            "input": "I was charged twice this month.",
            "reference": "Acknowledge and escalate to billing team.",
        },
        {
            "id": "case-002",
            "category": "technical",
            "input": "The export feature is broken.",
            "context": "User is on the Pro plan. Export was working last week.",
            "reference": "Check plan, then troubleshoot export steps.",
        },
    ]


@pytest.fixture
def sample_config():
    return {
        "experiment": {"name": "test-experiment"},
        "model": {"name": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 512},
        "prompts": {
            "prompt_a": {
                "name": "Minimal",
                "system": "You are a helpful assistant.",
            },
            "prompt_b": {
                "name": "Detailed",
                "system": "You are a detailed helpful assistant.",
            },
        },
        "test_set": "test_sets/support_5.yaml",
        "rubric": "rubrics/support.yaml",
    }


@pytest.fixture
def mock_llm_response():
    return {
        "response": "This is a mock response.",
        "input_tokens": 10,
        "output_tokens": 20,
        "latency_seconds": 0.5,
        "model": "gpt-4o-mini",
        "stop_reason": "end_turn",
    }
