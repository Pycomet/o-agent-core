import json
from typing import Optional, List
import logging

from ..llm.client import LLMClient, LLMMessage
from ..tools.registry import ToolRegistry
from .state import ExecutionState
from ..schemas.responses import TaskResult, ExecutionStep as ExecutionStepSchema

logger = logging.getLogger(__name__)


class Agent:
    """
    LLM-powered agent that can plan and execute tasks using tools.

    The agent:
    - Accepts a natural language goal
    - Uses an LLM to decide which tools to call and in what order
    - Maintains a complete execution trace
    - Returns structured results suitable for AI CEO analysis
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: int = 5,
    ):
        self.llm_client = llm_client
        self.tool_registry = tool_registry or ToolRegistry()
        self.max_iterations = max_iterations

    async def execute_task(
        self,
        goal: str,
        context: Optional[str] = None,
        tool_filter: Optional[List[str]] = None,
    ) -> TaskResult:
        """
        Execute a task using the agent.

        This method is idempotent - same goal + context produces the same result
        (assuming deterministic tool behavior and LLM temperature=0).

        Args:
            goal: Natural language description of the task
            context: Optional additional context
            tool_filter: Optional list of tool names to restrict usage

        Returns:
            TaskResult with status, output, and complete trace
        """
        state = ExecutionState()

        try:
            # Build system message
            system_msg = self._build_system_message()

            # Build user message
            user_msg = f"Goal: {goal}"
            if context:
                user_msg += f"\n\nContext: {context}"

            # Initialize conversation
            messages = [
                LLMMessage(role="system", content=system_msg),
                LLMMessage(role="user", content=user_msg),
            ]

            # Get available tools
            tool_definitions = self.tool_registry.get_tool_definitions(tool_filter)

            # Main execution loop
            iteration = 0
            while iteration < self.max_iterations:
                iteration += 1

                # Get LLM response (low temperature for repeatable tool selection)
                response = await self.llm_client.generate_with_tools(
                    messages=messages,
                    tools=tool_definitions,
                    temperature=0.2,
                )

                # Check if LLM wants to call tools
                if response.tool_calls:
                    # Assistant message with tool_calls must precede the tool responses
                    messages.append(
                        LLMMessage(
                            role="assistant",
                            content=response.content or "",
                            tool_calls=response.tool_calls,
                        )
                    )

                    for tool_call in response.tool_calls:
                        function_name = tool_call["function"]["name"]
                        tool_call_id = tool_call.get("id")

                        try:
                            function_args = json.loads(
                                tool_call["function"]["arguments"]
                            )
                        except json.JSONDecodeError as e:
                            error_msg = f"Invalid JSON in tool arguments: {e}"
                            state.add_tool_call_step(
                                tool_name=function_name,
                                tool_args={},
                                error=error_msg,
                            )
                            messages.append(
                                LLMMessage(
                                    role="tool",
                                    content=json.dumps({"error": error_msg}),
                                    name=function_name,
                                    tool_call_id=tool_call_id,
                                )
                            )
                            continue

                        try:
                            result = await self.tool_registry.execute_tool(
                                function_name, function_args
                            )
                            state.add_tool_call_step(
                                tool_name=function_name,
                                tool_args=function_args,
                                result=result,
                            )
                            messages.append(
                                LLMMessage(
                                    role="tool",
                                    content=json.dumps(result),
                                    name=function_name,
                                    tool_call_id=tool_call_id,
                                )
                            )
                        except Exception as e:
                            error_msg = str(e)
                            state.add_tool_call_step(
                                tool_name=function_name,
                                tool_args=function_args,
                                error=error_msg,
                            )
                            messages.append(
                                LLMMessage(
                                    role="tool",
                                    content=json.dumps({"error": error_msg}),
                                    name=function_name,
                                    tool_call_id=tool_call_id,
                                )
                            )

                    continue

                # No tool calls - LLM provided final answer
                if response.content:
                    state.add_final_answer(response.content)
                    state.set_success(response.content)
                    break
                else:
                    # No content and no tool calls - unusual
                    state.set_error("LLM returned empty response")
                    break

            # Check if we hit max iterations
            if iteration >= self.max_iterations and state.status == "running":
                state.set_partial(
                    output=state.final_output or "Task incomplete",
                    error=f"Maximum iterations ({self.max_iterations}) reached",
                )

        except Exception as e:
            logger.exception("Agent execution failed")
            state.set_error(f"Agent execution failed: {str(e)}")

        # Convert to TaskResult
        return self._state_to_result(state)

    def _build_system_message(self) -> str:
        """Build the system message for the LLM"""
        return """You are an AI agent that accomplishes tasks using the tools available to you.

When given a goal:
1. Decide which tool(s) to call.
2. Call them — one at a time, or in parallel when independent.
3. Once you have what you need, synthesize a clear, concise final answer.

If a tool fails, try a different approach or explain the limitation in your final answer."""

    def _state_to_result(self, state: ExecutionState) -> TaskResult:
        """Convert ExecutionState to TaskResult schema"""
        # Convert ExecutionStep objects to schema format
        trace_items = [ExecutionStepSchema(**step.model_dump()) for step in state.steps]

        return TaskResult(
            status=state.status,
            output=state.final_output or "",
            trace=trace_items,
            error=state.error,
        )
