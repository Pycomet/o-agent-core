"""Trigger.dev job definitions for agent execution"""

import os
from typing import Optional, List
import logging

# Note: trigger SDK imports (would be used in production)
# from trigger import job

from ..agent.core import Agent
from ..llm.factory import get_default_llm_client, LLMClientFactory
from ..llm.client import LLMClient
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _create_agent(
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
    tools: Optional[List[str]] = None,
) -> Agent:
    """
    Factory function to create an agent with specified configuration.

    Args:
        llm_provider: LLM provider ('openai', 'sovereign', etc.)
        llm_model: Model name
        tools: Optional list of tool names to register

    Returns:
        Configured Agent instance
    """
    # Create LLM client using factory
    llm_client = LLMClientFactory.create_client(
        provider=llm_provider,
        model=llm_model,
    )

    # Create tool registry
    tool_registry = ToolRegistry()

    # Create and return agent
    return Agent(llm_client=llm_client, tool_registry=tool_registry)


# @job("run-agent-task")
async def run_agent_task(
    goal: str,
    context: Optional[str] = None,
    tools: Optional[List[str]] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> dict:
    """
    Primary agent execution job for Trigger.dev.

    This job is:
    - Idempotent: Same inputs produce same outputs
    - Retriable: Can be safely retried on failure
    - Observable: Returns complete execution trace

    Args:
        goal: Natural language task description
        context: Optional additional context
        tools: Optional list of tool names to restrict usage
        llm_provider: Optional LLM provider override ('openai', 'sovereign')
        llm_model: Optional model name override

    Returns:
        Serialized TaskResult as dictionary
    """
    try:
        # Create agent with specified or default LLM client
        agent = _create_agent(
            llm_provider=llm_provider,
            llm_model=llm_model,
        )

        # Execute task
        result = await agent.execute_task(
            goal=goal,
            context=context,
            tool_filter=tools,
        )

        # Return serialized result with metadata
        return {
            **result.model_dump(),
            "metadata": {
                "llm_provider": llm_provider
                or os.getenv("LLMCLIENT_PROVIDER", "openai"),
                "llm_model": llm_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            },
        }

    except Exception as e:
        logger.exception("Trigger.dev job failed")
        return {
            "status": "error",
            "output": "",
            "trace": [],
            "error": f"Job execution failed: {str(e)}",
        }


# @job("scheduled-governance-audit")
async def scheduled_governance_audit(
    llm_provider: Optional[str] = None,
) -> dict:
    """
    Example scheduled job for AI-led governance workflows.

    Can be configured to use different LLM providers for different
    governance workflows

    Args:
        llm_provider: Optional LLM provider ('openai', 'sovereign')

    Returns:
        Dictionary with audit results
    """
    try:
        # Create agent with specified provider
        agent = _create_agent(llm_provider=llm_provider)

        # Example: Analyze governance activity
        result = await agent.execute_task(
            goal="Generate a summary of recent governance activity",
            context="This is a scheduled audit task",
        )

        return {
            "audit_status": "completed",
            "findings": result.output,
            "trace": [step.model_dump() for step in result.trace],
            "llm_provider": llm_provider or "default",
        }

    except Exception as e:
        logger.exception("Governance audit job failed")
        return {
            "audit_status": "error",
            "error": str(e),
        }


# Additional job examples for AI-led organization:

# @job("proposal-review")
async def proposal_review_job(
    proposal_id: str,
    proposal_content: str,
    llm_provider: Optional[str] = None,
) -> dict:
    """
    Review a governance proposal using specified LLM provider.


    Args:
        proposal_id: Unique proposal identifier
        proposal_content: Full proposal text
        llm_provider: Optional LLM provider

    Returns:
        Review results
    """
    agent = _create_agent(llm_provider=llm_provider)

    result = await agent.execute_task(
        goal=f"Review governance proposal {proposal_id} and add assessment notes",
        context=f"Proposal content: {proposal_content}",
        tool_filter=["governance_note"],
    )

    return result.model_dump()


# @job("multi-agent-task")
async def multi_agent_coordination(
    tasks: List[str],
    llm_provider: Optional[str] = None,
) -> dict:
    """
    Coordinate multiple agent tasks using same or different LLM providers.

    Args:
        tasks: List of task descriptions
        llm_provider: Optional LLM provider for all tasks

    Returns:
        Combined results from all tasks
    """
    results = []
    agent = _create_agent(llm_provider=llm_provider)

    for i, task in enumerate(tasks):
        result = await agent.execute_task(goal=task)
        results.append(
            {
                "task_index": i,
                "task": task,
                "result": result.model_dump(),
            }
        )

    return {
        "total_tasks": len(tasks),
        "results": results,
        "llm_provider": llm_provider or "default",
    }
