"""Tests for built-in tools."""

import pytest

from src.tools.math_tool import MathTool


@pytest.mark.asyncio
async def test_math_tool_basic():
    tool = MathTool()

    result = await tool.execute({"expression": "2 + 2"})
    assert result["result"] == 4.0

    result = await tool.execute({"expression": "(10 * 5) / 2"})
    assert result["result"] == 25.0


@pytest.mark.asyncio
async def test_math_tool_invalid():
    tool = MathTool()

    with pytest.raises(ValueError):
        await tool.execute({"expression": "import os"})

    with pytest.raises(ValueError):
        await tool.execute({"expression": "1 / 0"})


@pytest.mark.asyncio
async def test_tool_schemas():
    tool = MathTool()

    assert tool.name
    assert tool.description
    assert tool.parameters_schema

    openai_format = tool.to_openai_format()
    assert openai_format["type"] == "function"
    assert "function" in openai_format
    assert "name" in openai_format["function"]
    assert "description" in openai_format["function"]
    assert "parameters" in openai_format["function"]
