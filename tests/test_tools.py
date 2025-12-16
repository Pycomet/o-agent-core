"""Tests for tool implementations"""

import pytest
from src.tools.math_tool import MathTool
from src.tools.web_search import WebSearchTool
from src.tools.governance_tool import GovernanceNoteTool
from src.storage.memory import governance_store


@pytest.mark.asyncio
async def test_math_tool_basic():
    """Test basic math operations"""
    tool = MathTool()
    
    result = await tool.execute({"expression": "2 + 2"})
    assert result["result"] == 4.0
    
    result = await tool.execute({"expression": "(10 * 5) / 2"})
    assert result["result"] == 25.0


@pytest.mark.asyncio
async def test_math_tool_invalid():
    """Test math tool with invalid expressions"""
    tool = MathTool()
    
    with pytest.raises(ValueError):
        await tool.execute({"expression": "import os"})
    
    with pytest.raises(ValueError):
        await tool.execute({"expression": "1 / 0"})


@pytest.mark.asyncio
async def test_web_search_tool():
    """Test web search tool"""
    tool = WebSearchTool()
    
    result = await tool.execute({"query": "Python best practices"})
    
    assert "results" in result
    assert "count" in result
    assert len(result["results"]) > 0
    assert "title" in result["results"][0]
    assert "snippet" in result["results"][0]
    assert "url" in result["results"][0]


@pytest.mark.asyncio
async def test_governance_tool():
    """Test governance note tool"""
    tool = GovernanceNoteTool()
    
    # Clear any existing notes
    governance_store.clear()
    
    # Add a note
    result = await tool.execute({
        "proposal_id": "test-proposal-1",
        "note": "Approved by technical review"
    })
    
    assert result["success"] is True
    assert result["proposal_id"] == "test-proposal-1"
    assert result["total_notes"] == 1
    
    # Add another note
    result = await tool.execute({
        "proposal_id": "test-proposal-1",
        "note": "Approved by governance committee"
    })
    
    assert result["total_notes"] == 2
    
    # Verify notes are stored
    notes = governance_store.get_notes("test-proposal-1")
    assert len(notes) == 2


@pytest.mark.asyncio
async def test_tool_schemas():
    """Test that all tools have valid schemas"""
    tools = [MathTool(), WebSearchTool(), GovernanceNoteTool()]
    
    for tool in tools:
        assert tool.name
        assert tool.description
        assert tool.parameters_schema
        
        # Verify OpenAI format
        openai_format = tool.to_openai_format()
        assert openai_format["type"] == "function"
        assert "function" in openai_format
        assert "name" in openai_format["function"]
        assert "description" in openai_format["function"]
        assert "parameters" in openai_format["function"]

