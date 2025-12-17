from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
import os

from ..agent.core import Agent
from ..llm.factory import get_default_llm_client
from ..tools.registry import ToolRegistry
from ..schemas.requests import RunTaskRequest
from ..schemas.responses import TaskResult, GovernanceNotesResponse
from ..storage.memory import governance_store

logger = logging.getLogger(__name__)

router = APIRouter()


def get_agent() -> Agent:
    """
    Dependency injection for Agent instance.

    Uses factory to create LLM client based on environment configuration.
    This allows easy switching between OpenAI, or other providers.
    """
    try:
        llm_client = get_default_llm_client()
        tool_registry = ToolRegistry()
        return Agent(llm_client=llm_client, tool_registry=tool_registry)
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize agent")


@router.post("/run-task", response_model=TaskResult)
async def run_task(
    request: RunTaskRequest,
    agent: Agent = Depends(get_agent),
) -> TaskResult:
    """
    Execute an agent task.

    Args:
        request: Task request with goal, optional context, and tool filter
        agent: Agent instance (injected)

    Returns:
        TaskResult with status, output, and trace
    """
    try:
        logger.info(f"Executing task: {request.goal[:100]}...")

        result = await agent.execute_task(
            goal=request.goal,
            context=request.context,
            tool_filter=request.tools,
        )

        logger.info(f"Task completed with status: {result.status}")
        return result

    except Exception as e:
        logger.exception("Task execution failed")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.get("/governance-notes/{proposal_id}", response_model=GovernanceNotesResponse)
async def get_governance_notes(proposal_id: str) -> GovernanceNotesResponse:
    """
    Retrieve all governance notes for a proposal.

    Args:
        proposal_id: Unique identifier for the proposal

    Returns:
        GovernanceNotesResponse with all notes for the proposal
    """
    try:
        notes = governance_store.get_notes(proposal_id)

        return GovernanceNotesResponse(
            proposal_id=proposal_id,
            notes=notes,
            count=len(notes),
        )

    except Exception as e:
        logger.exception(f"Failed to retrieve notes for {proposal_id}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve governance notes: {str(e)}"
        )


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "o-agent-core",
    }
