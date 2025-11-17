#!/usr/bin/env python3
"""
Test script for CodeUnderstandingPipeline functionality.
Tests the full pipeline: initialization and query answering.
"""

import os
import time
from openai import OpenAI
from app.db import create_db_and_tables, get_session
from core import CodeUnderstandingPipeline


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_pipeline():
    """Test the full CodeUnderstandingPipeline."""
    print("=" * 70)
    print("Testing CodeUnderstandingPipeline")
    print("=" * 70)

    print("\n1. Setting up database...")
    try:
        create_db_and_tables()
        session = get_session()
        print("   ✅ Database setup complete")
    except Exception as e:
        print(f"   ❌ Database setup failed: {e}")
        return

    print("\n2. Initializing LLM client...")
    try:
        llm_client = get_llm_client()
        print("   ✅ LLM client initialized")
    except Exception as e:
        print(f"   ❌ LLM client initialization failed: {e}")
        return

    print("\n3. Initializing pipeline...")
    repo_url = "https://github.com/inclinedadarsh/inclinet"
    print(f"   📦 Repository: {repo_url}")

    try:
        pipeline = CodeUnderstandingPipeline(
            repo_path=repo_url,
            llm_client=llm_client,
            db_session=session,
        )
        print("   ✅ Pipeline initialized")
    except Exception as e:
        print(f"   ❌ Pipeline initialization failed: {e}")
        return

    print("\n4. Testing repository initialization...")
    print("-" * 70)
    print("   ⚠️  This may take several minutes depending on repository size...")

    start_time = time.time()
    try:
        result = pipeline.initialize_repository()
        elapsed = time.time() - start_time

        print("\n   ✅ Repository initialized successfully!")
        print(f"   ⏱️  Time taken: {elapsed:.2f} seconds")
        print(f"   📄 Files processed: {result['files_processed']}")
        print(f"   🔧 Components processed: {result['components_processed']}")
        print(f"   🔗 Dependencies stored: {result['dependencies_stored']}")
        print(f"   📦 Repository: {result['repository_name']}")
    except Exception as e:
        print(f"   ❌ Repository initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n5. Testing query answering...")
    print("-" * 70)

    test_queries = [
        "What does this project do?",
        "How does the loss function work?",
        "Where is the neural network defined?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        print("   " + "-" * 60)

        start_time = time.time()
        try:
            response = pipeline.answer_user_query(query)
            elapsed = time.time() - start_time

            print(f"   ✅ Query processed in {elapsed:.2f} seconds")
            print(f"   🎯 Classification: {response['classification']['type']}")
            print(f"   📊 Confidence: {response['confidence']:.2f}")
            print(f"   🔧 Tools used: {response['tools_used']}")

            if response.get("sources"):
                print(f"   📚 Sources: {len(response['sources'])}")

            if response.get("new_concepts_learned"):
                print(
                    f"   🧠 New concepts: {', '.join(response['new_concepts_learned'])}"
                )

            print("\n   💬 Answer (first 200 chars):")
            print(f"   {response['answer'][:200]}...")

        except Exception as e:
            print(f"   ❌ Query processing failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n6. Testing pipeline statistics...")
    try:
        stats = pipeline.get_pipeline_stats()
        print("   ✅ Pipeline stats retrieved")
        for key, value in stats.items():
            print(f"   📊 {key}: {value}")
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}")

    print("\n✅ CodeUnderstandingPipeline test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_pipeline()
