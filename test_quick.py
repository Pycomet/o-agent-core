"""Quick test of the agent core without Vercel AI SDK"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_simple():
    """Test simple generation without tools"""
    print("\n" + "="*60)
    print("TEST 1: Simple Generation (No Tools)")
    print("="*60)
    
    # This would use the simple llm-generate task
    print("✅ This test requires Trigger.dev to be running")
    print("   Run: npx trigger.dev@latest dev")
    print("   Then trigger tasks via dashboard or API")

async def test_local_tools():
    """Test tools locally without LLM"""
    print("\n" + "="*60)
    print("TEST 2: Local Tool Execution (No LLM)")
    print("="*60)
    
    from src.tools.math_tool import MathTool
    from src.tools.web_search import WebSearchTool
    from src.tools.governance_tool import GovernanceNoteTool
    
    # Test MathTool
    math_tool = MathTool()
    result = await math_tool.execute({"expression": "10 + 5 * 2"})
    print(f"✅ MathTool: 10 + 5 * 2 = {result['result']}")
    
    # Test WebSearchTool
    search_tool = WebSearchTool()
    result = await search_tool.execute({"query": "Python testing"})
    print(f"✅ WebSearchTool: Found {result['count']} results")
    
    # Test GovernanceNoteTool
    gov_tool = GovernanceNoteTool()
    result = await gov_tool.execute({
        "proposal_id": "test-123",
        "note": "Quick test note"
    })
    print(f"✅ GovernanceNoteTool: Added note to {result['proposal_id']}")

async def test_fastapi():
    """Test FastAPI endpoints"""
    print("\n" + "="*60)
    print("TEST 3: FastAPI Endpoints")
    print("="*60)
    
    print("Start FastAPI server:")
    print("  python main.py")
    print("\nThen test endpoints:")
    print("  curl http://localhost:8000/health")
    print("  curl http://localhost:8000/api/v1/governance-notes/test-123")

async def main():
    print("\n╔═══════════════════════════════════════════════════════════╗")
    print("║         O-Agent Core - Quick Test Suite              ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    await test_simple()
    await test_local_tools()
    await test_fastapi()
    
    print("\n" + "="*60)
    print("✅ Local tests complete!")
    print("="*60)
    print("\nFor full integration tests with LLM:")
    print("1. Install Node.js dependencies: cd trigger && npm install && cd ..")
    print("2. Set environment variables in .env")
    print("3. Start Trigger.dev: npx trigger.dev@latest dev")
    print("4. Run FastAPI: python main.py")
    print("5. Test via Trigger.dev dashboard")

if __name__ == "__main__":
    asyncio.run(main())
