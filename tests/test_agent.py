"""Tests for agent core"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.agent.core import Agent
from src.agent.state import ExecutionState
from src.llm.client import LLMClient, LLMMessage, LLMResponse
from src.tools.registry import ToolRegistry
from src.tools.math_tool import MathTool


class MockLLMClient(LLMClient):
    """Mock LLM client for testing"""
    
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
    
    async def generate(self, messages, temperature=0.7, max_tokens=None):
        response = self.responses[self.call_count] if self.call_count < len(self.responses) else self.responses[-1]
        self.call_count += 1
        return response
    
    async def generate_with_tools(self, messages, tools, temperature=0.7, max_tokens=None):
        response = self.responses[self.call_count] if self.call_count < len(self.responses) else self.responses[-1]
        self.call_count += 1
        return response


@pytest.mark.asyncio
async def test_agent_simple_task():
    """Test agent with a simple task (no tool calls)"""
    mock_llm = MockLLMClient([
        LLMResponse(
            content="The answer is 42",
            finish_reason="stop"
        )
    ])
    
    agent = Agent(llm_client=mock_llm)
    result = await agent.execute_task(goal="What is the answer?")
    
    assert result.status == "success"
    assert "42" in result.output
    assert len(result.trace) > 0


@pytest.mark.asyncio
async def test_agent_with_tool_call():
    """Test agent making a tool call"""
    mock_llm = MockLLMClient([
        # First response: tool call
        LLMResponse(
            content=None,
            tool_calls=[{
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "math",
                    "arguments": '{"expression": "2 + 2"}'
                }
            }],
            finish_reason="tool_calls"
        ),
        # Second response: final answer
        LLMResponse(
            content="The result of 2 + 2 is 4",
            finish_reason="stop"
        )
    ])
    
    # Use real tool registry with MathTool
    tool_registry = ToolRegistry(tools=[MathTool()])
    agent = Agent(llm_client=mock_llm, tool_registry=tool_registry)
    
    result = await agent.execute_task(goal="Calculate 2 + 2")
    
    assert result.status == "success"
    assert len(result.trace) >= 2  # At least tool call + final answer
    
    # Verify tool call step
    tool_step = next((s for s in result.trace if s.action == "tool_call"), None)
    assert tool_step is not None
    assert tool_step.tool_name == "math"


@pytest.mark.asyncio
async def test_execution_state():
    """Test execution state management"""
    state = ExecutionState()
    
    assert state.status == "running"
    assert state.current_step == 0
    
    state.add_tool_call_step("math", {"expression": "2 + 2"}, result={"value": 4})
    assert state.current_step == 1
    
    state.add_final_answer("The answer is 4")
    assert state.current_step == 2
    assert state.final_output == "The answer is 4"
    
    state.set_success("Complete")
    assert state.status == "success"
    
    trace = state.get_trace()
    assert len(trace) == 2

