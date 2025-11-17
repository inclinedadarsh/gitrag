from openai import OpenAI
from sqlmodel import Session, create_engine
from core.db_manager import DatabaseManager
from core.classifier import QueryClassifier
from core.retrieval import RetrievalEngine
from app.db import create_db_and_tables

# Setup database connection
engine = create_engine("sqlite:///database.db")
create_db_and_tables()
session = Session(engine)

# Initialize components
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# Initialize classifier and retrieval engine
db_manager = DatabaseManager(session)
classifier = QueryClassifier(client)
retrieval_engine = RetrievalEngine(db_manager)

print("\n=== Testing RetrievalEngine ===\n")

# Test different query types
test_queries = [
    "What does this project do?",
    "How does the loss function work?",
    "Where is the neural network defined?",
    "Trace the execution flow of training",
]

for i, query in enumerate(test_queries, 1):
    print(f"Query {i}: '{query}'")

    # Classify the query
    classification = classifier.classify_query(query)
    print(
        f"Classification: {classification['type']} (confidence: {classification['confidence']})"
    )

    # Retrieve context
    context = retrieval_engine.retrieve_context(classification)
    print("Retrieved context:")
    print(f"  - Entry point: {context.get('entry_point')}")
    print(f"  - Token count: {context.get('token_count', 0)}")

    if context.get("repo_summary"):
        print(f"  - Repository summary: {context['repo_summary'].text[:100]}...")

    if context.get("file_summaries"):
        print(f"  - File summaries: {len(context['file_summaries'])} files")
        for i, file_summary in enumerate(context["file_summaries"][:3]):
            print(f"    {i + 1}. {file_summary.target_id}: {file_summary.text[:50]}...")

    if context.get("component_summary"):
        print(f"  - Component: {context['component_summary'].target_id}")
        print(f"    Summary: {context['component_summary'].text[:100]}...")
        if context.get("code_location"):
            print(
                f"    Location: {context['code_location'].filepath}:{context['code_location'].line_start}-{context['code_location'].line_end}"
            )
        if context.get("dependencies"):
            print(f"    Dependencies: {len(context['dependencies'])} components")
        if context.get("dependents"):
            print(f"    Dependents: {len(context['dependents'])} components")

    if context.get("search_results"):
        print(f"  - Search results: {len(context['search_results'])} matches")
        for i, result in enumerate(context["search_results"][:3]):
            print(
                f"    {i + 1}. {result['summary'].target_id} (relevance: {result['relevance']:.2f}): {result['summary'].text[:50]}..."
            )

    if context.get("execution_path"):
        print(f"  - Execution path: {len(context['execution_path'])} components")
        for i, step in enumerate(context["execution_path"][:5]):
            print(
                f"    {i + 1}. [{step['depth']}] {step['summary'].target_id}: {step['summary'].text[:50]}..."
            )
        if context.get("call_chain"):
            print(f"    Call chain: {context['call_chain']}")

    if context.get("error"):
        print(f"  - Error: {context['error']}")
    if context.get("fallback_suggestions"):
        print(f"  - Fallback suggestions: {context['fallback_suggestions']}")

    print("-" * 60)

# Show retrieval stats
print("\n=== Retrieval Engine Stats ===")
stats = retrieval_engine.get_retrieval_stats()
for key, value in stats.items():
    print(f"{key}: {value}")

print("\nDone!")
