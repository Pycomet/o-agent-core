"""Execution state and trace management"""

from typing import List, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    """Single step in the agent execution trace"""

    step: int = Field(..., description="Step number in execution sequence")
    action: Literal["tool_call", "reasoning", "final_answer"] = Field(
        ..., description="Type of action performed"
    )
    tool_name: Optional[str] = Field(
        None, description="Name of tool called (if action=tool_call)"
    )
    tool_args: Optional[dict] = Field(
        None, description="Arguments passed to tool"
    )
    result: Optional[Any] = Field(
        None, description="Result from tool or reasoning"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp",
    )
    error: Optional[str] = Field(None, description="Error message if step failed")


class ExecutionState:
    """
    Tracks the execution state of an agent task.
    
    Maintains a step-by-step trace of all actions, tool calls,
    and reasoning performed during task execution.
    """

    def __init__(self):
        self.steps: List[ExecutionStep] = []
        self.current_step: int = 0
        self.status: Literal["running", "success", "error", "partial"] = "running"
        self.final_output: Optional[str] = None
        self.error: Optional[str] = None

    def add_reasoning_step(self, reasoning: str) -> None:
        """
        Add a reasoning step to the trace.
        
        Args:
            reasoning: The reasoning content (can be redacted in production)
        """
        self.current_step += 1
        step = ExecutionStep(
            step=self.current_step,
            action="reasoning",
            result=reasoning,
        )
        self.steps.append(step)

    def add_tool_call_step(
        self,
        tool_name: str,
        tool_args: dict,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Add a tool call step to the trace.
        
        Args:
            tool_name: Name of the tool called
            tool_args: Arguments passed to the tool
            result: Result from tool execution (if successful)
            error: Error message (if failed)
        """
        self.current_step += 1
        step = ExecutionStep(
            step=self.current_step,
            action="tool_call",
            tool_name=tool_name,
            tool_args=tool_args,
            result=result,
            error=error,
        )
        self.steps.append(step)

    def add_final_answer(self, answer: str) -> None:
        """
        Add the final answer step.
        
        Args:
            answer: The final answer/output from the agent
        """
        self.current_step += 1
        step = ExecutionStep(
            step=self.current_step,
            action="final_answer",
            result=answer,
        )
        self.steps.append(step)
        self.final_output = answer

    def set_success(self, output: str) -> None:
        """
        Mark execution as successful.
        
        Args:
            output: Final output message
        """
        self.status = "success"
        self.final_output = output

    def set_error(self, error: str) -> None:
        """
        Mark execution as failed.
        
        Args:
            error: Error message
        """
        self.status = "error"
        self.error = error

    def set_partial(self, output: str, error: str) -> None:
        """
        Mark execution as partially successful.
        
        Args:
            output: Partial output achieved
            error: Error that prevented full completion
        """
        self.status = "partial"
        self.final_output = output
        self.error = error

    def get_trace(self) -> List[ExecutionStep]:
        """Get the complete execution trace"""
        return self.steps.copy()

    def to_dict(self) -> dict:
        """
        Convert state to dictionary format.
        
        Returns:
            Dictionary containing status, output, trace, and error
        """
        return {
            "status": self.status,
            "output": self.final_output or "",
            "trace": [step.model_dump() for step in self.steps],
            "error": self.error,
        }

