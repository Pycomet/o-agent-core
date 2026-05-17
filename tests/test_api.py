"""Tests for API endpoints"""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.routes import get_agent
from src.schemas.responses import TaskResult, ExecutionStep

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "o-agent-core"


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_run_task_endpoint():
    mock_agent = AsyncMock()
    mock_agent.execute_task.return_value = TaskResult(
        status="success",
        output="Test output",
        trace=[
            ExecutionStep(
                step=1,
                action="final_answer",
                result="Test output",
                timestamp="2024-01-15T10:00:00Z",
            )
        ],
    )

    app.dependency_overrides[get_agent] = lambda: mock_agent
    try:
        response = client.post(
            "/api/v1/run-task",
            json={"goal": "Test task", "context": "Test context"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["output"] == "Test output"


def test_run_task_invalid_request():
    # Override agent so body validation runs without needing real env config
    app.dependency_overrides[get_agent] = lambda: AsyncMock()
    try:
        response = client.post("/api/v1/run-task", json={})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422
