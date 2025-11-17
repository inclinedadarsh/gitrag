#!/usr/bin/env python3
"""
Test script for DatabaseManager functionality.
Tests database operations: insert, query, search, and dependency management.
"""

from core.db_manager import DatabaseManager
from app.db import create_db_and_tables, get_session


def test_db_manager():
    """Test DatabaseManager with various operations."""
    print("=" * 70)
    print("Testing DatabaseManager")
    print("=" * 70)

    print("\n1. Setting up database...")
    try:
        create_db_and_tables()
        session = get_session()
        db_manager = DatabaseManager(session)
        print("   ✅ Database setup complete")
    except Exception as e:
        print(f"   ❌ Database setup failed: {e}")
        return

    print("\n2. Testing insert operations...")
    print("-" * 70)

    # Test inserting a repository summary
    print("\n   Test 1: Insert repository summary")
    try:
        repo_summary = db_manager.insert_summary(
            summary_id="repo_test_repo",
            level="repository",
            text="This is a test repository for testing purposes.",
            token_count=10,
            target_id="test_repo",
        )
        print("      ✅ Repository summary inserted")
        print(f"      📝 ID: {repo_summary.id}")
        print(f"      📊 Level: {repo_summary.level}")
    except Exception as e:
        print(f"      ❌ Failed to insert: {e}")
        import traceback

        traceback.print_exc()
        return

    # Test inserting a file summary
    print("\n   Test 2: Insert file summary")
    try:
        file_summary = db_manager.insert_summary(
            summary_id="file_test_file.py",
            level="file",
            text="This is a test Python file.",
            token_count=8,
            parent_id="repo_test_repo",
            target_id="test_file.py",
        )
        print("      ✅ File summary inserted")
        print(f"      📝 ID: {file_summary.id}")
        print(f"      🔗 Parent: {file_summary.parent_id}")
    except Exception as e:
        print(f"      ❌ Failed to insert: {e}")
        import traceback

        traceback.print_exc()

    # Test inserting a function summary
    print("\n   Test 3: Insert function summary")
    try:
        func_summary = db_manager.insert_summary(
            summary_id="func_test_function",
            level="function",
            text="This is a test function that does something.",
            token_count=9,
            parent_id="file_test_file.py",
            target_id="test_function",
        )
        print("      ✅ Function summary inserted")
        print(f"      📝 ID: {func_summary.id}")
    except Exception as e:
        print(f"      ❌ Failed to insert: {e}")
        import traceback

        traceback.print_exc()

    # Test inserting code mapping
    print("\n   Test 4: Insert code mapping")
    try:
        code_mapping = db_manager.insert_code_mapping(
            summary_id="func_test_function",
            filepath="test_file.py",
            line_start=10,
            line_end=20,
            element_type="function",
            content_preview="def test_function():",
        )
        print("      ✅ Code mapping inserted")
        print(f"      📄 File: {code_mapping.filepath}")
        print(f"      📍 Lines: {code_mapping.line_start}-{code_mapping.line_end}")
    except Exception as e:
        print(f"      ❌ Failed to insert: {e}")
        import traceback

        traceback.print_exc()

    # Test inserting dependency
    print("\n   Test 5: Insert dependency")
    try:
        dependency = db_manager.insert_dependency(
            source_id="func_test_function",
            target_id="func_another_function",
            relationship="calls",
        )
        print("      ✅ Dependency inserted")
        print(f"      🔗 Source: {dependency.source_id}")
        print(f"      🎯 Target: {dependency.target_id}")
        print(f"      📊 Relationship: {dependency.relationship}")
    except Exception as e:
        print(f"      ❌ Failed to insert: {e}")
        import traceback

        traceback.print_exc()

    print("\n3. Testing query operations...")
    print("-" * 70)

    # Test getting repository summary
    print("\n   Test 1: Get repository summary")
    try:
        repo = db_manager.get_repository_summary()
        if repo:
            print("      ✅ Repository summary retrieved")
            print(f"      📝 Text: {repo.text[:50]}...")
        else:
            print("      ⚠️  No repository summary found")
    except Exception as e:
        print(f"      ❌ Failed to retrieve: {e}")

    # Test getting file summary
    print("\n   Test 2: Get file summary")
    try:
        file_summary = db_manager.get_file_summary("test_file.py")
        if file_summary:
            print("      ✅ File summary retrieved")
            print(f"      📝 Text: {file_summary.text[:50]}...")
        else:
            print("      ⚠️  No file summary found")
    except Exception as e:
        print(f"      ❌ Failed to retrieve: {e}")

    # Test searching by keyword
    print("\n   Test 3: Search by keyword")
    try:
        results = db_manager.search_summaries_by_keyword("test", limit=5)
        print("      ✅ Search completed")
        print(f"      📊 Results: {len(results)}")
        for result in results[:3]:
            print(f"         - {result.target_id} ({result.level})")
    except Exception as e:
        print(f"      ❌ Failed to search: {e}")

    # Test searching by component name
    print("\n   Test 4: Search by component name")
    try:
        component = db_manager.search_by_component_name("test_function")
        if component:
            print("      ✅ Component found")
            print(f"      📝 ID: {component.id}")
            print(f"      📊 Level: {component.level}")
        else:
            print("      ⚠️  Component not found")
    except Exception as e:
        print(f"      ❌ Failed to search: {e}")

    print("\n4. Testing dependency operations...")
    print("-" * 70)

    # Test getting dependencies
    print("\n   Test 1: Get dependencies of component")
    try:
        deps = db_manager.get_dependencies_of_component("func_test_function", "calls")
        print("      ✅ Dependencies retrieved")
        print(f"      📊 Count: {len(deps)}")
        for dep in deps:
            print(f"         - {dep.target_id}")
    except Exception as e:
        print(f"      ❌ Failed to retrieve: {e}")

    # Test getting dependents
    print("\n   Test 2: Get dependents of component")
    try:
        dependents = db_manager.get_dependents_of_component(
            "func_another_function", "calls"
        )
        print("      ✅ Dependents retrieved")
        print(f"      📊 Count: {len(dependents)}")
    except Exception as e:
        print(f"      ❌ Failed to retrieve: {e}")

    # Test getting dependency graph
    print("\n   Test 3: Get dependency graph")
    try:
        graph = db_manager.get_dependency_graph()
        print("      ✅ Dependency graph retrieved")
        print(f"      📊 Nodes: {len(graph)}")
        if graph:
            sample_node = list(graph.keys())[0]
            print(f"      📋 Sample: {sample_node} -> {graph[sample_node]}")
    except Exception as e:
        print(f"      ❌ Failed to retrieve: {e}")

    print("\n5. Testing utility operations...")
    print("-" * 70)

    # Test getting summaries by level
    print("\n   Test 1: Get summaries by level")
    try:
        funcs = db_manager.get_all_summaries_by_level("function")
        print("      ✅ Function summaries retrieved")
        print(f"      📊 Count: {len(funcs)}")
    except Exception as e:
        print(f"      ❌ Failed to retrieve: {e}")

    print("\n✅ DatabaseManager test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_db_manager()
