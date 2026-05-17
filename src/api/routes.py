from fastapi import APIRouter, HTTPException, Depends
import logging

from ..agent.core import Agent
from ..llm.factory import get_default_llm_client
from ..tools.registry import ToolRegistry
from ..schemas.requests import RunTaskRequest
from ..schemas.responses import TaskResult

logger = logging.getLogger(__name__)

router = APIRouter()


def get_agent() -> Agent:
    """Dependency injection for an Agent instance."""
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
    """Execute an agent task and return the final answer plus execution trace."""
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


@router.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "o-agent-core"}
