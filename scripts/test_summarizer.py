#!/usr/bin/env python3
"""
Test script for SummaryGenerator functionality.
Tests repository, file, and component summary generation.
"""

import os
from openai import OpenAI
from core.summarizer import SummaryGenerator
from core.parser import CodeParser


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_summarizer():
    """Test SummaryGenerator with sample data."""
    print("=" * 70)
    print("Testing SummaryGenerator")
    print("=" * 70)

    print("\n1. Initializing LLM client...")
    try:
        llm_client = get_llm_client()
        summarizer = SummaryGenerator(llm_client)
        print("   ✅ SummaryGenerator initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return

    print("\n2. Parsing a small repository for test data...")
    try:
        parser = CodeParser("https://github.com/inclinedadarsh/inclinet")
        parsed_repo = parser.parse_repository()
        print(f"   ✅ Repository parsed: {len(parsed_repo['files'])} files")
    except Exception as e:
        print(f"   ❌ Failed to parse repository: {e}")
        return

    print("\n3. Testing repository summary generation...")
    try:
        repo_summary = summarizer.generate_repository_summary(parsed_repo)
        print("   ✅ Repository summary generated")
        print(f"   📝 Summary (first 200 chars): {repo_summary[:200]}...")
    except Exception as e:
        print(f"   ❌ Failed to generate repository summary: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n4. Testing file summary generation...")
    python_files = [f for f in parsed_repo["files"] if f.get("type") == "python"]
    if python_files:
        try:
            sample_file = python_files[0]
            file_summary = summarizer.generate_file_summary_compact(sample_file)
            print("   ✅ File summary generated")
            print(f"   📄 File: {sample_file['filepath']}")
            print(f"   📝 Summary: {file_summary}")
        except Exception as e:
            print(f"   ❌ Failed to generate file summary: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("   ⚠️  No Python files found to test")

    print("\n5. Testing component summary generation...")
    if python_files:
        sample_file = python_files[0]
        functions = sample_file.get("functions", [])
        if functions:
            try:
                sample_func = functions[0]
                func_summary = summarizer.generate_component_summary(
                    sample_func, "function"
                )
                print("   ✅ Component summary generated")
                print(f"   🔧 Function: {sample_func.get('name')}")
                print(f"   📝 Summary: {func_summary}")
            except Exception as e:
                print(f"   ❌ Failed to generate component summary: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("   ⚠️  No functions found to test")
    else:
        print("   ⚠️  No Python files found to test")

    print("\n✅ SummaryGenerator test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_summarizer()
