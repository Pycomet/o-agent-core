"""Response schemas for API and agent results"""

from typing import Optional, Any, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ExecutionStep(BaseModel):
    """Single step in agent execution trace"""

    step: int = Field(..., description="Step number in execution sequence")
    action: Literal["tool_call", "reasoning", "final_answer"] = Field(
        ..., description="Type of action performed"
    )
    tool_name: Optional[str] = Field(
        None, description="Name of tool called (if action=tool_call)"
    )
    tool_args: Optional[dict] = Field(None, description="Arguments passed to tool")
    result: Optional[Any] = Field(None, description="Result from tool or reasoning")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp of when step occurred",
    )
    error: Optional[str] = Field(None, description="Error message if step failed")

    class Config:
        json_schema_extra = {
            "example": {
                "step": 1,
                "action": "tool_call",
                "tool_name": "math",
                "tool_args": {"expression": "2 + 2"},
                "result": {"value": 4},
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class TaskResult(BaseModel):
    """Final result from agent task execution"""

    status: Literal["success", "error", "partial"] = Field(
        ..., description="Overall execution status"
    )
    output: str = Field(..., description="Final output or answer from the agent")
    trace: List[ExecutionStep] = Field(
        default_factory=list, description="Complete execution trace"
    )
    error: Optional[str] = Field(None, description="Error message if execution failed")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "output": "The result is 4",
                "trace": [
                    {
                        "step": 1,
                        "action": "tool_call",
                        "tool_name": "math",
                        "tool_args": {"expression": "2 + 2"},
                        "result": {"value": 4},
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                ],
            }
        }


