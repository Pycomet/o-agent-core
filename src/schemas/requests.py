from typing import Optional, List
from pydantic import BaseModel, Field


class RunTaskRequest(BaseModel):
    """Request schema for running an agent task"""

    goal: str = Field(
        ...,
        description="Natural language description of the task to accomplish",
        min_length=1,
    )
    context: Optional[str] = Field(
        None, description="Optional additional context for the task"
    )
    tools: Optional[List[str]] = Field(
        None,
        description="Optional list of tool names to restrict usage to. If None, all tools are available",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "goal": "Calculate the square root of 144 and search for its significance",
                "context": "User is learning about perfect squares",
                "tools": ["math", "web_search"],
            }
        }

