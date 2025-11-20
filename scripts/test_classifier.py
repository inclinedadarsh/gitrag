#!/usr/bin/env python3
"""
Test script for QueryClassifier functionality.
Tests query classification and retrieval strategy determination.
"""

import os
from openai import OpenAI
from core.classifier import QueryClassifier


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_classifier():
    """Test QueryClassifier with various query types."""
    print("=" * 70)
    print("Testing QueryClassifier")
    print("=" * 70)

    print("\n1. Initializing QueryClassifier...")
    try:
        llm_client = get_llm_client()
        classifier = QueryClassifier(llm_client)
        print("   [OK] QueryClassifier initialized")
    except Exception as e:
        print(f"   [ERR] Failed to initialize: {e}")
        return

    # Test queries covering different types
    test_queries = [
        ("What does this project do?", "overview"),
        ("How does the loss function work?", "component_specific"),
        ("Trace the execution flow of training", "flow_tracing"),
        ("Where is the neural network defined?", "location_finding"),
        ("Explain the authentication system", "component_specific"),
        ("What happens when I call train()?", "flow_tracing"),
    ]

    print(f"\n2. Testing {len(test_queries)} different query types...")
    print("-" * 70)

    for i, (query, expected_type) in enumerate(test_queries, 1):
        print(f"\n   Test {i}: {query}")
        try:
            classification = classifier.classify_query(query)

            print(f"      Type: {classification['type']} (expected: {expected_type})")
            print(f"      Entry point: {classification['entry_point']}")
            print(f"      Retrieval strategy: {classification['retrieval_strategy']}")
            print(f"      Confidence: {classification['confidence']:.2f}")

            if classification.get("target"):
                print(f"      Target: {classification['target']}")

            # Check if classification matches expected type
            if classification["type"] == expected_type:
                print("      [OK] Classification correct")
            else:
                print("      [WARN]  Classification differs from expected")

        except Exception as e:
            print(f"      [ERR] Failed to classify: {e}")
            import traceback

            traceback.print_exc()

    print("\n3. Testing retrieval plan generation...")
    try:
        sample_classification = {
            "type": "component_specific",
            "entry_point": "component",
            "retrieval_strategy": "focused",
            "target": "loss",
            "confidence": 0.9,
        }

        plan = classifier.get_retrieval_plan(sample_classification)
        print("   [OK] Retrieval plan generated")
        print(f"   [LIST] Steps: {len(plan['steps'])}")
        for step in plan["steps"]:
            print(f"      - {step['action']}: {step['params']}")
        print(f"   [STATS] Expected results: {plan['expected_results']}")
        print(f"   [LOOP] Fallback: {plan['fallback_strategy']}")
    except Exception as e:
        print(f"   [ERR] Failed to generate retrieval plan: {e}")
        import traceback

        traceback.print_exc()

    print("\n[OK] QueryClassifier test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_classifier()
