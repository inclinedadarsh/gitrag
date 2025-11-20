#!/usr/bin/env python3
"""
Test script for CodeParser functionality.
Tests repository parsing, file parsing, and dependency graph building.
"""

from core.parser import CodeParser


def test_parser():
    """Test CodeParser with a sample repository."""
    print("=" * 70)
    print("Testing CodeParser")
    print("=" * 70)

    # Test with a small repository
    repo_url = "https://github.com/inclinedadarsh/inclinet"

    print(f"\n1. Initializing parser with: {repo_url}")
    try:
        parser = CodeParser(repo_url)
        print("   [OK] Parser initialized")
        print(f"   [PATH] Repository path: {parser.repo_path}")
    except Exception as e:
        print(f"   [ERR] Failed to initialize parser: {e}")
        return

    print("\n2. Parsing repository...")
    try:
        parsed_repo = parser.parse_repository()
        print("   [OK] Repository parsed successfully")
        print(f"   [STATS] Files found: {len(parsed_repo['files'])}")
        print(f"   [PKG] Repository name: {parsed_repo['repository']['name']}")
    except Exception as e:
        print(f"   [ERR] Failed to parse repository: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n3. Analyzing parsed data...")
    python_files = [f for f in parsed_repo["files"] if f.get("type") == "python"]
    markdown_files = [f for f in parsed_repo["files"] if f.get("type") == "markdown"]

    print(f"   [FILE] Python files: {len(python_files)}")
    print(f"   [NOTE] Markdown files: {len(markdown_files)}")

    total_functions = sum(len(f.get("functions", [])) for f in python_files)
    total_classes = sum(len(f.get("classes", [])) for f in python_files)

    print(f"   [TOOL] Functions found: {total_functions}")
    print(f"   [STRUCT]  Classes found: {total_classes}")

    print("\n4. Testing dependency graph...")
    dependency_graph = parsed_repo.get("dependency_graph", {})
    print(f"   [STATS] Files with dependencies: {len(dependency_graph)}")

    if dependency_graph:
        sample_file = list(dependency_graph.keys())[0]
        print(f"   [LIST] Sample: {sample_file}")
        print(f"      Dependencies: {dependency_graph[sample_file][:3]}...")

    print("\n5. Testing file parsing...")
    if python_files:
        sample_file = python_files[0]
        print(f"   [FILE] Sample file: {sample_file['filepath']}")
        print(f"      Functions: {len(sample_file.get('functions', []))}")
        print(f"      Classes: {len(sample_file.get('classes', []))}")
        print(f"      Imports: {len(sample_file.get('imports', []))}")

    print("\n[OK] CodeParser test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_parser()
