#!/usr/bin/env python3
"""
Test script for the FastAPI application.
"""

import requests
import time

# API base URL
BASE_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test health check endpoint."""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_initialize():
    """Test repository initialization."""
    print("🔍 Testing repository initialization...")

    payload = {
        "repo_path": "https://github.com/inclinedadarsh/inclinet",
        "user_id": "test_user",
    }

    response = requests.post(f"{BASE_URL}/initialize", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    return response.status_code == 200


def test_query():
    """Test query endpoint."""
    print("🔍 Testing query endpoint...")

    queries = [
        "What does this project do?",
        "How does the loss function work?",
        "Where is the neural network defined?",
        "What are the main components of this library?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")

        payload = {"query": query, "user_id": "test_user"}

        response = requests.post(f"{BASE_URL}/query", json=payload)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data['answer'][:100]}...")
            print(f"Confidence: {data['confidence']}")
            print(f"Tools used: {data['tools_used']}")
            print(f"Processing time: {data['processing_time']:.2f}s")
        else:
            print(f"Error: {response.text}")

        print("-" * 50)


def test_component():
    """Test component details endpoint."""
    print("🔍 Testing component details...")

    components = ["loss", "NeuralNet", "train"]

    for component in components:
        print(f"Component: {component}")
        response = requests.get(f"{BASE_URL}/component/{component}")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Summary: {data['summary'][:100]}...")
            print(f"File: {data['file_path']}")
            print(f"Dependencies: {data['dependencies']}")
        else:
            print(f"Error: {response.text}")

        print("-" * 30)


def test_user_knowledge():
    """Test user knowledge endpoint."""
    print("🔍 Testing user knowledge...")

    response = requests.get(f"{BASE_URL}/user/test_user/knowledge")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def main():
    """Run all tests."""
    print("=== GitRAG API Test Suite ===\n")

    # Test health check
    test_health()

    # Test initialization
    if test_initialize():
        print("✅ Repository initialized successfully\n")

        # Wait a moment for initialization to complete
        time.sleep(2)

        # Test queries
        test_query()

        # Test component details
        test_component()

        # Test user knowledge
        test_user_knowledge()

    else:
        print("❌ Repository initialization failed")

    print("✅ Test suite completed!")


if __name__ == "__main__":
    main()
