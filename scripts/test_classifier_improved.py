from openai import OpenAI
from core.classifier import QueryClassifier

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)
classifier = QueryClassifier(client)

# Test the same queries as before
test_queries = [
    "How does loss works?",
    "how to setup the project locally?",
    "how does the back propagation work?",
    "What does this project do?",
    "Where is the User class defined?",
    "Trace the execution flow of authenticate_user",
    "Explain the loss function",
]

print("=== Testing Improved QueryClassifier ===\n")

for i, query in enumerate(test_queries, 1):
    print(f"Query {i}: '{query}'")
    result = classifier.classify_query(query)
    print(f"Type: {result['type']}")
    print(f"Target: {result.get('target', 'None')}")
    print(f"Confidence: {result['confidence']}")
    print(f"Entry Point: {result['entry_point']}")
    print(f"Retrieval Strategy: {result['retrieval_strategy']}")
    print(f"Needs Code: {result['needs_code']}")
    print(f"Needs Full Context: {result['needs_full_context']}")
    print("-" * 50)

# Test retrieval plan for one query
print("\n=== Retrieval Plan Example ===")
plan = classifier.get_retrieval_plan(classifier.classify_query("How does loss works?"))
print("Plan for 'How does loss works?':")
print(f"Steps: {plan['steps']}")
print(f"Expected Results: {plan['expected_results']}")
print(f"Fallback Strategy: {plan['fallback_strategy']}")
