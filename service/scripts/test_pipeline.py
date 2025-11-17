from openai import OpenAI
from sqlmodel import Session, create_engine
from core import CodeUnderstandingPipeline
from app.db import create_db_and_tables
import time

print("=== GitRAG Service Pipeline Test ===\n")

# Setup
print("1. Setting up database connection...")
engine = create_engine("sqlite:///database.db")
create_db_and_tables()
session = Session(engine)
print("✓ Database connection established")

# Initialize LLM client
print("\n2. Initializing LLM client...")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)
print("✓ OpenRouter client initialized")

# Initialize pipeline
print("\n3. Initializing CodeUnderstandingPipeline...")
pipeline = CodeUnderstandingPipeline(
    repo_path="https://github.com/inclinedadarsh/inclinet",
    llm_client=client,
    db_session=session,
)
print("✓ Pipeline initialized with all components:")
print("  - CodeParser")
print("  - SummaryGenerator")
print("  - DatabaseManager")
print("  - QueryClassifier")
print("  - RetrievalEngine")
print("  - LLMAgent")

# Test queries
test_queries = [
    "What does this project do?",
    "How does the loss function work?",
    "Where is the neural network defined?",
    "Trace the execution flow of training",
    "What are the main components of this neural network library?",
]

print(f"\n4. Starting query processing with {len(test_queries)} test queries...")
print("=" * 80)

for i, query in enumerate(test_queries, 1):
    print(f"\n🔍 QUERY {i}: '{query}'")
    print("=" * 50)

    start_time = time.time()

    try:
        print("\n📝 Step 1: Processing query through pipeline...")
        response = pipeline.answer_user_query(query)

        processing_time = time.time() - start_time

        print(f"\n📊 RESULTS for Query {i}:")
        print(f"  ⏱️  Processing time: {processing_time:.2f} seconds")
        print(
            f"  🎯 Classification: {response['classification']['type']} (confidence: {response['classification']['confidence']})"
        )
        print(f"  🔧 Tools used: {response['tools_used']}")
        print(f"  🧠 New concepts learned: {response['new_concepts_learned']}")
        print(f"  📈 Confidence: {response['confidence']}")

        print("\n💬 ANSWER:")
        print(f"  {response['answer']}")

        if response["sources"]:
            print(f"\n📚 SOURCES USED ({len(response['sources'])} items):")
            for j, source in enumerate(
                response["sources"][:5], 1
            ):  # Show first 5 sources
                print(
                    f"  {j}. {source.target_id} ({source.level}): {source.text[:60]}..."
                )
            if len(response["sources"]) > 5:
                print(f"  ... and {len(response['sources']) - 5} more sources")

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"\n❌ ERROR in Query {i} (after {processing_time:.2f}s):")
        print(f"  {e}")
        import traceback

        print(f"  Traceback: {traceback.format_exc()}")

    print("\n" + "=" * 80)

# Show pipeline stats
print("\n5. 📊 PIPELINE STATISTICS:")
print("=" * 50)
stats = pipeline.get_pipeline_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n✅ TEST COMPLETED SUCCESSFULLY!")
print("=" * 80)
