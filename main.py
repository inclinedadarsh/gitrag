#!/usr/bin/env python3
"""
GitRAG Terminal Application
Interactive terminal interface for code understanding and question answering.
"""

import os
import sys
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from core.db import create_db_and_tables, get_session
from core import CodeUnderstandingPipeline

# Load environment variables from .env file if it exists
load_dotenv()


def get_llm_client() -> OpenAI:
    """Initialize LLM client from environment or use default."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is not set.\n"
            "Please set it using one of the following methods:\n"
            "  1. Export it: export OPENROUTER_API_KEY='your-api-key'\n"
            "  2. Create a .env file with: OPENROUTER_API_KEY=your-api-key\n"
            "  3. Pass it when running: OPENROUTER_API_KEY='your-api-key' python main.py"
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def print_banner():
    """Print welcome banner."""
    print("=" * 70)
    print("  GitRAG - AI-Powered Code Understanding and Question Answering")
    print("=" * 70)
    print()


def print_help():
    """Print help message."""
    print("\nCommands:")
    print("  /help     - Show this help message")
    print("  /reset    - Reset and initialize a new repository")
    print("  /exit     - Exit the application")
    print("  /quit     - Exit the application")
    print("\nOr simply ask a question about the codebase!\n")


def initialize_repository(pipeline: CodeUnderstandingPipeline, repo_url: str) -> bool:
    """Initialize repository with the provided URL."""
    import time

    print(f"\n🔄 Initializing repository: {repo_url}")
    print("This may take a few minutes depending on repository size...\n")

    start_time = time.time()

    try:
        result = pipeline.initialize_repository()
        elapsed_time = time.time() - start_time

        # Display summary table
        print("\n" + "=" * 70)
        print("Initialization Complete!")
        print("=" * 70)
        print(f"\n{'Metric':<35} {'Count':<15}")
        print("-" * 70)
        print(f"{'Repository':<35} {result['repository_name']:<15}")
        print(f"{'Files Processed':<35} {result['files_processed']:<15}")
        print(f"{'Functions Processed':<35} {result.get('functions_processed', 0):<15}")
        print(f"{'Classes Processed':<35} {result.get('classes_processed', 0):<15}")
        print(f"{'Total Components':<35} {result['components_processed']:<15}")
        print(f"{'Dependencies Stored':<35} {result['dependencies_stored']:<15}")
        print(f"{'Time Taken':<35} {elapsed_time:.2f}s{'':<10}")
        print("=" * 70)
        print()

        return True

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ Error initializing repository (after {elapsed_time:.2f}s): {e}")

        # Check if it's a UNIQUE constraint error (database already has data)
        if "UNIQUE constraint" in str(e) or "IntegrityError" in str(type(e).__name__):
            print("\n⚠️  Database already contains data for this repository.")
            print("   Use /reset to clear the database and start fresh.")

        import traceback

        traceback.print_exc()
        return False


def process_query(pipeline: CodeUnderstandingPipeline, query: str) -> None:
    """Process a user query and display results."""
    import time

    print("\n" + "=" * 70)
    print("Processing Query")
    print("=" * 70)
    print(f"\n🔍 Query: {query}\n")

    start_time = time.time()

    try:
        response = pipeline.answer_user_query(query)
        elapsed_time = time.time() - start_time

        print("\n" + "=" * 70)
        print("Answer")
        print("=" * 70)
        print(f"\n{response['answer']}\n")
        print("=" * 70)

        # Show metadata in a clean format
        print("\n📊 Query Details:")
        print(f"   Classification: {response['classification']['type']}")
        print(f"   Confidence: {response.get('confidence', 0.0):.2f}")
        print(f"   Processing time: {elapsed_time:.2f}s")

        if response.get("tools_used"):
            print(f"   Tools used: {', '.join(response['tools_used'])}")

        if response.get("sources"):
            print(f"\n📚 Sources ({len(response['sources'])} total):")
            for i, source in enumerate(response["sources"][:5], 1):
                print(f"   {i}. {source.target_id} ({source.level})")
            if len(response["sources"]) > 5:
                print(f"   ... and {len(response['sources']) - 5} more")

        if response.get("new_concepts_learned"):
            print(
                f"\n🧠 New concepts learned: {', '.join(response['new_concepts_learned'])}"
            )

        print()

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n❌ Error processing query (after {elapsed_time:.2f}s): {e}")
        import traceback

        traceback.print_exc()
        print()


def main():
    """Main application loop."""
    print_banner()

    # Setup database
    print("🔧 Setting up database...")
    try:
        create_db_and_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)

    # Initialize LLM client
    print("🔧 Initializing LLM client...")
    try:
        llm_client = get_llm_client()
        print("✅ LLM client initialized")
    except Exception as e:
        print(f"❌ LLM client initialization failed: {e}")
        sys.exit(1)

    # Get database session
    session = get_session()

    # Initialize pipeline (will be set up with repo later)
    pipeline: Optional[CodeUnderstandingPipeline] = None

    print("\n✅ Setup complete!\n")
    print_help()

    # Main loop
    initialized = False

    while True:
        try:
            if not initialized:
                # Need to initialize repository first
                print("\n" + "=" * 70)
                print("Repository Initialization")
                print("=" * 70)
                print("\nEnter a GitHub repository URL to analyze:")
                print("(Example: https://github.com/username/repository)")

                repo_url = input("\nRepository URL (or /help for commands): ").strip()

                if repo_url in ["/help", "/h"]:
                    print_help()
                    continue
                elif repo_url in ["/exit", "/quit", "/q"]:
                    print("\n👋 Goodbye!")
                    break
                elif not repo_url:
                    continue

                if not (
                    repo_url.startswith("http://") or repo_url.startswith("https://")
                ):
                    print("❌ Invalid URL. Please provide a full GitHub URL.")
                    continue

                # Initialize pipeline with repository
                pipeline = CodeUnderstandingPipeline(
                    repo_path=repo_url,
                    llm_client=llm_client,
                    db_session=session,
                )

                if initialize_repository(pipeline, repo_url):
                    initialized = True
                    print("\n" + "=" * 70)
                    print("Ready for Questions!")
                    print("=" * 70)
                    print("\n💡 You can now ask questions about the codebase!")
                    print("   Type /help for commands or /exit to quit.\n")
                else:
                    pipeline = None
                    continue
            else:
                # Ready for queries
                query = input("\n💬 Ask a question (or /help for commands): ").strip()

                if not query:
                    continue

                if query in ["/help", "/h"]:
                    print_help()
                    continue
                elif query in ["/reset", "/r"]:
                    print("\n🔄 Resetting database...")
                    try:
                        # Clear all data from database
                        from models import Summary, Dependency, CodeMapping
                        from sqlmodel import select

                        # Delete all dependencies
                        deps = session.exec(select(Dependency)).all()
                        for dep in deps:
                            session.delete(dep)

                        # Delete all code mappings
                        mappings = session.exec(select(CodeMapping)).all()
                        for mapping in mappings:
                            session.delete(mapping)

                        # Delete all summaries
                        summaries = session.exec(select(Summary)).all()
                        for summary in summaries:
                            session.delete(summary)

                        session.commit()

                        pipeline = None
                        initialized = False
                        print(
                            "✅ Database cleared. Please initialize a new repository.\n"
                        )
                    except Exception as e:
                        print(f"❌ Error resetting database: {e}")
                        print("   You may need to delete database.db manually.\n")
                    continue
                elif query in ["/exit", "/quit", "/q"]:
                    print("\n👋 Goodbye!")
                    break
                else:
                    process_query(pipeline, query)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback

            traceback.print_exc()
            print()

    # Cleanup
    if session:
        session.close()


if __name__ == "__main__":
    main()
