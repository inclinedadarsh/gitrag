from openai import OpenAI
from core.classifier import QueryClassifier

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)
classifier = QueryClassifier(client)

# Classify different query types
result1 = classifier.classify_query("How does loss works?")
print(result1)
# Returns: {"type": "flow_tracing", "target": "authentication", "confidence": 0.9, ...}

result2 = classifier.classify_query("how to setup the project locally?")
print(result2)
# Returns: {"type": "component_specific", "target": "login", "confidence": 0.95, ...}

result3 = classifier.classify_query("how does the back propagation work?")
print(result3)
# Returns: {"type": "location_finding", "target": "User", "confidence": 0.9, ...}

# Get detailed retrieval plan
plan = classifier.get_retrieval_plan(result1)
print(plan)
# Returns: {"steps": [...], "expected_results": "...", "fallback_strategy": "..."}
