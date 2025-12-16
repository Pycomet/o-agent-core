"""
O-Agent Core - Complete Examples using Vercel AI SDK v5

This file demonstrates all three tools and the multi-runtime architecture:
- Python Agent orchestrates tasks
- Trigger.dev routes to Node.js jobs
- Vercel AI SDK v5 handles LLM communication

Run these examples after:
1. Setting up .env with OPENAI_API_KEY and TRIGGER_API_KEY
2. Installing Node dependencies: cd trigger && npm install && cd ..
3. Starting Trigger.dev: npx trigger.dev@latest dev (in separate terminal)
4. Running this script: python examples_vercel.py
"""

import asyncio
import os
from dotenv import load_dotenv
from src.agent.core import Agent
from src.llm.factory import get_default_llm_client
from src.tools.registry import ToolRegistry
from src.storage.memory import governance_store

# Load environment
load_dotenv()


async def example_1_math():
    """Example 1: Single tool usage - Math calculation"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Single Tool Usage (Math)")
    print("=" * 70)
    print("Goal: Calculate the square root of 144")
    print()
    
    try:
        llm_client = get_default_llm_client()
        tool_registry = ToolRegistry()
        agent = Agent(llm_client=llm_client, tool_registry=tool_registry)
        
        result = await agent.execute_task(
            goal="Calculate the square root of 144",
            tool_filter=["math"]  # Restrict to math tool only
        )
        
        print(f"Status: {result.status}")
        print(f"Output: {result.output}")
        print(f"\n📊 Execution Trace ({len(result.trace)} steps):")
        for step in result.trace:
            print(f"  Step {step.step}: {step.action}")
            if step.tool_name:
                print(f"    🔧 Tool: {step.tool_name}")
                print(f"    📥 Args: {step.tool_args}")
                print(f"    📤 Result: {step.result}")
        
        await llm_client.close()
        return result.status == "success"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def example_2_multi_tool():
    """Example 2: Multi-tool usage - Search and Math"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Multi-Tool Usage (Search + Math)")
    print("=" * 70)
    print("Goal: Search for Python and calculate square of result count")
    print()
    
    try:
        llm_client = get_default_llm_client()
        tool_registry = ToolRegistry()
        agent = Agent(llm_client=llm_client, tool_registry=tool_registry)
        
        result = await agent.execute_task(
            goal="Search for 'Python best practices' and calculate the square of the number of results found",
            context="User wants to understand search volume",
            tool_filter=["web_search", "math"]
        )
        
        print(f"Status: {result.status}")
        print(f"Output: {result.output}")
        print(f"\n📊 Execution Trace ({len(result.trace)} steps):")
        for step in result.trace:
            print(f"  Step {step.step}: {step.action}")
            if step.tool_name:
                print(f"    🔧 Tool: {step.tool_name}")
                if step.tool_name == "web_search" and step.result:
                    print(f"    📥 Query: {step.tool_args.get('query')}")
                    print(f"    📤 Found: {step.result.get('count', 0)} results")
                elif step.tool_name == "math":
                    print(f"    📥 Expression: {step.tool_args.get('expression')}")
                    print(f"    📤 Result: {step.result.get('result')}")
        
        await llm_client.close()
        return result.status == "success"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def example_3_governance():
    """Example 3: Governance note tool"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Governance Note Tool")
    print("=" * 70)
    print("Goal: Add governance note to proposal")
    print()
    
    try:
        # Clear previous notes
        governance_store.clear()
        
        llm_client = get_default_llm_client()
        tool_registry = ToolRegistry()
        agent = Agent(llm_client=llm_client, tool_registry=tool_registry)
        
        result = await agent.execute_task(
            goal="Add a governance note to proposal-456 saying: Approved by technical committee on December 16, 2025",
            tool_filter=["governance_note"]
        )
        
        print(f"Status: {result.status}")
        print(f"Output: {result.output}")
        print(f"\n📊 Execution Trace ({len(result.trace)} steps):")
        for step in result.trace:
            print(f"  Step {step.step}: {step.action}")
            if step.tool_name:
                print(f"    🔧 Tool: {step.tool_name}")
                print(f"    📥 Proposal ID: {step.tool_args.get('proposal_id')}")
                print(f"    📝 Note: {step.tool_args.get('note')}")
        
        # Verify note was stored
        notes = governance_store.get_notes("proposal-456")
        print(f"\n💾 Stored Notes for proposal-456: {len(notes)}")
        for i, note in enumerate(notes, 1):
            print(f"  Note {i}: {note['note']}")
            print(f"    🕒 Timestamp: {note['timestamp']}")
        
        await llm_client.close()
        return result.status == "success" and len(notes) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def example_4_all_tools():
    """Example 4: Using all three tools in one task"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: All Three Tools Combined")
    print("=" * 70)
    print("Goal: Complex task using math, search, and governance")
    print()
    
    try:
        # Clear previous notes
        governance_store.clear()
        
        llm_client = get_default_llm_client()
        tool_registry = ToolRegistry()
        agent = Agent(llm_client=llm_client, tool_registry=tool_registry)
        
        result = await agent.execute_task(
            goal=(
                "First, calculate 8 * 7. "
                "Then search for 'AI agents' and note how many results. "
                "Finally, add a governance note to proposal-789 summarizing what you found."
            ),
            context="Testing all three tools in sequence",
            tool_filter=["math", "web_search", "governance_note"]
        )
        
        print(f"Status: {result.status}")
        print(f"Output: {result.output}")
        print(f"\n📊 Execution Trace ({len(result.trace)} steps):")
        
        tools_used = set()
        for step in result.trace:
            print(f"  Step {step.step}: {step.action}")
            if step.tool_name:
                tools_used.add(step.tool_name)
                print(f"    🔧 Tool: {step.tool_name}")
                if step.tool_name == "math":
                    print(f"    📥 Expression: {step.tool_args.get('expression')}")
                    print(f"    📤 Result: {step.result.get('result')}")
                elif step.tool_name == "web_search":
                    print(f"    📥 Query: {step.tool_args.get('query')}")
                    print(f"    📤 Found: {step.result.get('count')} results")
                elif step.tool_name == "governance_note":
                    print(f"    📥 Proposal: {step.tool_args.get('proposal_id')}")
                    print(f"    📝 Note: {step.tool_args.get('note')[:60]}...")
        
        print(f"\n🎯 Tools Used: {', '.join(sorted(tools_used))}")
        
        # Show stored governance notes
        notes = governance_store.get_notes("proposal-789")
        if notes:
            print(f"\n💾 Final Governance Notes:")
            for note in notes:
                print(f"  • {note['note']}")
        
        await llm_client.close()
        return result.status == "success" and len(tools_used) >= 2
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all examples"""
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║     O-Agent Core - Vercel AI SDK v5 Integration Examples       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not set in environment")
        print("Please create a .env file with your OpenAI API key")
        return
    
    if not os.getenv("TRIGGER_API_KEY"):
        print("\n❌ ERROR: TRIGGER_API_KEY not set in environment")
        print("Please add TRIGGER_API_KEY to your .env file")
        print("Get one at: https://trigger.dev")
        return
    
    print("\n✅ Prerequisites checked")
    print("📡 Using Vercel AI SDK v5 via Trigger.dev multi-runtime architecture")
    print("🔄 Make sure Trigger.dev is running: npx trigger.dev@latest dev")
    print()
    
    input("Press Enter to start examples...")
    
    results = []
    
    # Run examples
    results.append(("Example 1: Math Tool", await example_1_math()))
    
    print("\n" + "─" * 70)
    input("Press Enter for next example...")
    
    results.append(("Example 2: Multi-Tool", await example_2_multi_tool()))
    
    print("\n" + "─" * 70)
    input("Press Enter for next example...")
    
    results.append(("Example 3: Governance", await example_3_governance()))
    
    print("\n" + "─" * 70)
    input("Press Enter for final example...")
    
    results.append(("Example 4: All Tools", await example_4_all_tools()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} examples passed")
    
    if total_passed == len(results):
        print("\n🎉 All examples completed successfully!")
        print("✨ Vercel AI SDK v5 integration is working perfectly!")
    else:
        print("\n⚠️  Some examples failed. Check the output above for details.")
        print("💡 Make sure Trigger.dev is running: npx trigger.dev@latest dev")


if __name__ == "__main__":
    asyncio.run(main())

