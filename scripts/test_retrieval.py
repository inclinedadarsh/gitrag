#!/usr/bin/env python3
"""
Test script for RetrievalEngine functionality.
Tests context retrieval based on different classification types.
"""

import os
from openai import OpenAI
from core.retrieval import RetrievalEngine
from core.db_manager import DatabaseManager
from app.db import create_db_and_tables, get_session


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_retrieval():
    """Test RetrievalEngine with different retrieval strategies."""
    print("=" * 70)
    print("Testing RetrievalEngine")
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

    print("\n2. Initializing RetrievalEngine...")
    try:
        retrieval = RetrievalEngine(db_manager)
        print("   ✅ RetrievalEngine initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    print("\n3. Testing retrieval strategies...")
    print("-" * 70)

    # Test repository overview retrieval
    print("\n   Test 1: Repository overview retrieval")
    try:
        context = retrieval.retrieve_repository_overview()
        print("      ✅ Context retrieved")
        print(f"      📊 Entry point: {context.get('entry_point')}")
        print(f"      📈 Token count: {context.get('token_count', 0)}")
        if context.get("repo_summary"):
            print(
                f"      📝 Repository summary: {context['repo_summary'].text[:100]}..."
            )
        if context.get("file_summaries"):
            print(f"      📄 File summaries: {len(context['file_summaries'])}")
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        import traceback

        traceback.print_exc()

    # Test component context retrieval
    print("\n   Test 2: Component context retrieval")
    try:
        # This will fail if no components exist, which is expected
        context = retrieval.retrieve_component_context("test_component")
        if context.get("error"):
            print(
                f"      ⚠️  Component not found (expected if DB is empty): {context['error']}"
            )
        else:
            print("      ✅ Component context retrieved")
            print(f"      📊 Entry point: {context.get('entry_point')}")
            print(f"      📈 Token count: {context.get('token_count', 0)}")
    except Exception as e:
        print(f"      ⚠️  Error (may be expected if DB is empty): {e}")

    # Test search retrieval
    print("\n   Test 3: Search retrieval")
    try:
        context = retrieval.retrieve_by_search("test")
        print("      ✅ Search results retrieved")
        print(f"      📊 Entry point: {context.get('entry_point')}")
        print(f"      📈 Token count: {context.get('token_count', 0)}")
        print(f"      🔍 Total matches: {context.get('total_matches', 0)}")
        if context.get("search_results"):
            print(f"      📋 Results: {len(context['search_results'])}")
    except Exception as e:
        print(f"      ⚠️  Error (may be expected if DB is empty): {e}")

    # Test execution trace retrieval
    print("\n   Test 4: Execution trace retrieval")
    try:
        context = retrieval.retrieve_execution_trace("test_component", max_depth=3)
        if context.get("error"):
            print(
                f"      ⚠️  Component not found (expected if DB is empty): {context['error']}"
            )
        else:
            print("      ✅ Execution trace retrieved")
            print(f"      📊 Entry point: {context.get('entry_point')}")
            print(f"      📈 Token count: {context.get('token_count', 0)}")
            if context.get("execution_path"):
                print(f"      🔗 Path length: {len(context['execution_path'])}")
    except Exception as e:
        print(f"      ⚠️  Error (may be expected if DB is empty): {e}")

    print("\n4. Testing retrieval stats...")
    try:
        stats = retrieval.get_retrieval_stats()
        print("   ✅ Retrieval stats retrieved")
        for key, value in stats.items():
            print(f"      {key}: {value}")
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}")
        import traceback

        traceback.print_exc()

    print("\n✅ RetrievalEngine test completed!")
    print("=" * 70)
    print("Note: Some tests may show warnings if the database is empty.")
    print("      This is expected. Initialize a repository first for full testing.")


if __name__ == "__main__":
    test_retrieval()
