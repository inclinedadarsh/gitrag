#!/usr/bin/env python3
"""
Test script for RetrievalEngine functionality.
Tests context retrieval based on different classification types.
"""

import os
from openai import OpenAI
from core.retrieval import RetrievalEngine
from core.db_manager import DatabaseManager
from app.db import create_db_and_tables, get_session
from utils.tui_logger import TUILogger


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_retrieval():
    """Test RetrievalEngine with different retrieval strategies."""
    mode = os.getenv("MODE", "production")
    logger = TUILogger(mode=mode)
    logger.show_logo()
    logger.rule("Testing RetrievalEngine", icon="🧪")

    logger.info("1. Setting up database...", icon="🗄️")
    try:
        create_db_and_tables()
        session = get_session()
        db_manager = DatabaseManager(session)
        logger.success("Database setup complete", indent=1)
    except Exception as e:
        logger.error(f"Database setup failed: {e}", indent=1)
        return

    logger.info("2. Initializing RetrievalEngine...", icon="⚙️")
    try:
        retrieval = RetrievalEngine(db_manager)
        logger.success("RetrievalEngine initialized", indent=1)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}", indent=1)
        return

    logger.rule("3. Testing retrieval strategies", icon="🧪")

    # Test repository overview retrieval
    logger.info("Test 1: Repository overview retrieval", icon="📦", indent=1)
    try:
        context = retrieval.retrieve_repository_overview()
        logger.success("Context retrieved", indent=2)
        logger.bullet(f"Entry point: {context.get('entry_point')}", indent=3)
        logger.bullet(f"Token count: {context.get('token_count', 0)}", indent=3)
        if context.get("repo_summary"):
            logger.bullet(
                f"Repository summary sample: {context['repo_summary'].text[:100]}...",
                indent=3,
            )
        if context.get("file_summaries"):
            logger.bullet(f"File summaries: {len(context['file_summaries'])}", indent=3)
    except Exception as e:
        logger.error(f"Failed: {e}", indent=2)
        import traceback

        traceback.print_exc()

    # Test component context retrieval
    logger.info("Test 2: Component context retrieval", icon="🧩", indent=1)
    try:
        # This will fail if no components exist, which is expected
        context = retrieval.retrieve_component_context("test_component")
        if context.get("error"):
            logger.warning(
                f"Component not found (expected if DB is empty): {context['error']}",
                indent=2,
            )
        else:
            logger.success("Component context retrieved", indent=2)
            logger.bullet(f"Entry point: {context.get('entry_point')}", indent=3)
            logger.bullet(f"Token count: {context.get('token_count', 0)}", indent=3)
    except Exception as e:
        logger.warning(f"Error (may be expected if DB is empty): {e}", indent=2)

    # Test search retrieval
    logger.info("Test 3: Search retrieval", icon="🔍", indent=1)
    try:
        context = retrieval.retrieve_by_search("test")
        logger.success("Search results retrieved", indent=2)
        logger.bullet(f"Entry point: {context.get('entry_point')}", indent=3)
        logger.bullet(f"Token count: {context.get('token_count', 0)}", indent=3)
        logger.bullet(f"Total matches: {context.get('total_matches', 0)}", indent=3)
        if context.get("search_results"):
            logger.bullet(f"Results: {len(context['search_results'])}", indent=3)
    except Exception as e:
        logger.warning(f"Error (may be expected if DB is empty): {e}", indent=2)

    # Test execution trace retrieval
    logger.info("Test 4: Execution trace retrieval", icon="🧵", indent=1)
    try:
        context = retrieval.retrieve_execution_trace("test_component", max_depth=3)
        if context.get("error"):
            logger.warning(
                f"Component not found (expected if DB is empty): {context['error']}",
                indent=2,
            )
        else:
            logger.success("Execution trace retrieved", indent=2)
            logger.bullet(f"Entry point: {context.get('entry_point')}", indent=3)
            logger.bullet(f"Token count: {context.get('token_count', 0)}", indent=3)
            if context.get("execution_path"):
                logger.bullet(
                    f"Path length: {len(context['execution_path'])}", indent=3
                )
    except Exception as e:
        logger.warning(f"Error (may be expected if DB is empty): {e}", indent=2)

    logger.info("4. Testing retrieval stats...", icon="📊")
    try:
        stats = retrieval.get_retrieval_stats()
        logger.success("Retrieval stats retrieved", indent=1)
        for key, value in stats.items():
            logger.bullet(f"{key}: {value}", indent=2)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", indent=1)
        import traceback

        traceback.print_exc()

    logger.success("RetrievalEngine test completed!", icon="✅")
    logger.warning(
        "Some tests may warn if the database is empty — initialize a repository for full coverage.",
        indent=0,
    )


if __name__ == "__main__":
    test_retrieval()
