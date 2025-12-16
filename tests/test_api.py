"""Tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.api.app import app
from src.schemas.responses import TaskResult, ExecutionStep
from src.storage.memory import governance_store

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()
    assert response.json()["service"] == "o-agent-core"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_governance_notes():
    """Test governance notes endpoint"""
    # Clear store
    governance_store.clear()
    
    # Add some notes
    governance_store.add_note("test-proposal", "Note 1")
    governance_store.add_note("test-proposal", "Note 2")
    
    # Retrieve notes
    response = client.get("/api/v1/governance-notes/test-proposal")
    assert response.status_code == 200
    
    data = response.json()
    assert data["proposal_id"] == "test-proposal"
    assert data["count"] == 2
    assert len(data["notes"]) == 2


@patch("src.api.routes.Agent")
def test_run_task_endpoint(mock_agent_class):
    """Test run-task endpoint with mocked agent"""
    # Mock agent response
    mock_agent = AsyncMock()
    mock_agent.execute_task.return_value = TaskResult(
        status="success",
        output="Test output",
        trace=[
            ExecutionStep(
                step=1,
                action="final_answer",
                result="Test output",
                timestamp="2024-01-15T10:00:00Z"
            )
        ]
    )
    mock_agent_class.return_value = mock_agent
    
    response = client.post(
        "/api/v1/run-task",
        json={
            "goal": "Test task",
            "context": "Test context"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["output"] == "Test output"


def test_run_task_invalid_request():
    """Test run-task with invalid request"""
    response = client.post(
        "/api/v1/run-task",
        json={}  # Missing required 'goal' field
    )
    
    assert response.status_code == 422  # Validation error

