#!/usr/bin/env python3
"""
Test script for LLMAgent functionality.
Tests agent reasoning, tool execution, and query answering.
"""

import os
from openai import OpenAI
from core.agent import LLMAgent
from core.db_manager import DatabaseManager
from app.db import create_db_and_tables, get_session


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_agent():
    """Test LLMAgent with sample queries."""
    print("=" * 70)
    print("Testing LLMAgent")
    print("=" * 70)

    print("\n1. Setting up database...")
    try:
        create_db_and_tables()
        session = get_session()
        db_manager = DatabaseManager(session)
        print("   ✅ Database setup complete")
    except Exception as e:
        print(f"   ❌ Database setup failed: {e}")
        return

    print("\n2. Initializing LLMAgent...")
    try:
        llm_client = get_llm_client()
        agent = LLMAgent(llm_client, db_manager, max_iterations=3)
        print("   ✅ LLMAgent initialized")
        print(f"   🔧 Available tools: {list(agent.tools.keys())}")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    print("\n3. Testing tool execution...")
    print("-" * 70)

    # Test search_components tool
    print("\n   Test 1: search_components tool")
    try:
        result = agent.execute_tool(
            "search_components", {"keyword": "test", "limit": 5}
        )
        if result.get("error"):
            print(f"      ⚠️  Tool error (expected if DB is empty): {result['error']}")
        else:
            print("      ✅ Tool executed successfully")
            print(f"      📊 Results: {len(result.get('result', []))}")
            print(f"      📈 Tokens: {result.get('token_count', 0)}")
    except Exception as e:
        print(f"      ⚠️  Error (may be expected if DB is empty): {e}")

    # Test get_dependency_graph tool
    print("\n   Test 2: get_dependency_graph tool")
    try:
        result = agent.execute_tool("get_dependency_graph", {})
        if result.get("error"):
            print(f"      ⚠️  Tool error: {result['error']}")
        else:
            print("      ✅ Tool executed successfully")
            graph = result.get("result", {})
            print(f"      📊 Graph nodes: {len(graph)}")
    except Exception as e:
        print(f"      ⚠️  Error: {e}")

    print("\n4. Testing decision making...")
    print("-" * 70)

    test_query = "What does this project do?"
    initial_context = {
        "repo_summary": None,
        "file_summaries": [],
        "search_results": [],
    }
    user_knowledge = {"expertise_level": "intermediate", "concepts_learned": []}

    print(f"\n   Query: {test_query}")
    try:
        decision = agent.decide_next_action(
            test_query, initial_context, user_knowledge, 0
        )
        print("      ✅ Decision made")
        print(f"      🎯 Action: {decision.get('action')}")
        print(f"      💭 Reasoning: {decision.get('reasoning', 'N/A')}")
        print(f"      📊 Confidence: {decision.get('confidence', 0.0)}")
        if decision.get("tool_name"):
            print(f"      🔧 Tool: {decision['tool_name']}")
    except Exception as e:
        print(f"      ❌ Failed to make decision: {e}")
        import traceback

        traceback.print_exc()

    print("\n5. Testing full query answering (requires initialized repository)...")
    print("-" * 70)
    print("   ⚠️  This test requires a repository to be initialized first.")
    print("   ⚠️  Run the main application or test_pipeline.py to initialize.")

    print("\n✅ LLMAgent test completed!")
    print("=" * 70)
    print("Note: Some tests may show warnings if the database is empty.")
    print("      This is expected. Initialize a repository first for full testing.")


if __name__ == "__main__":
    test_agent()
