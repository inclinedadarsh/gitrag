#!/usr/bin/env python3
"""
Test script for LLMAgent functionality.
Tests agent reasoning, tool execution, and query answering.
"""

import os
from openai import OpenAI
from core.agent import LLMAgent
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


def test_agent():
    """Test LLMAgent with sample queries."""
    mode = os.getenv("MODE", "production")
    logger = TUILogger(mode=mode)
    logger.show_logo()
    logger.rule("Testing LLMAgent", icon="🧪")

    logger.info("1. Setting up database...", icon="🗄️")
    try:
        create_db_and_tables()
        session = get_session()
        db_manager = DatabaseManager(session)
        logger.success("Database setup complete", indent=1)
    except Exception as e:
        logger.error(f"Database setup failed: {e}", indent=1)
        return

    logger.info("2. Initializing LLMAgent...", icon="🤖")
    try:
        llm_client = get_llm_client()
        agent = LLMAgent(llm_client, db_manager, max_iterations=3, logger=logger)
        logger.success("LLMAgent initialized", indent=1)
        logger.bullet(f"Available tools: {list(agent.tools.keys())}", indent=2)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}", indent=1)
        return

    logger.rule("3. Testing tool execution", icon="🧰")

    # Test search_components tool
    logger.info("Test 1: search_components tool", icon="🔍", indent=1)
    try:
        result = agent.execute_tool(
            "search_components", {"keyword": "test", "limit": 5}
        )
        if result.get("error"):
            logger.warning(
                f"Tool error (expected if DB is empty): {result['error']}", indent=2
            )
        else:
            logger.success("Tool executed successfully", indent=2)
            logger.bullet(f"Results: {len(result.get('result', []))}", indent=3)
            logger.bullet(f"Tokens: {result.get('token_count', 0)}", indent=3)
    except Exception as e:
        logger.warning(f"Error (may be expected if DB is empty): {e}", indent=2)

    # Test get_dependency_graph tool
    logger.info("Test 2: get_dependency_graph tool", icon="🔗", indent=1)
    try:
        result = agent.execute_tool("get_dependency_graph", {})
        if result.get("error"):
            logger.warning(f"Tool error: {result['error']}", indent=2)
        else:
            logger.success("Tool executed successfully", indent=2)
            graph = result.get("result", {})
            logger.bullet(f"Graph nodes: {len(graph)}", indent=3)
    except Exception as e:
        logger.warning(f"Error: {e}", indent=2)

    logger.rule("4. Testing decision making", icon="🧠")

    test_query = "What does this project do?"
    initial_context = {
        "repo_summary": None,
        "file_summaries": [],
        "search_results": [],
    }
    user_knowledge = {"expertise_level": "intermediate", "concepts_learned": []}

    logger.info(f"Query: {test_query}", icon="💬", indent=1)
    try:
        decision = agent.decide_next_action(
            test_query, initial_context, user_knowledge, 0
        )
        logger.success("Decision made", indent=2)
        logger.bullet(f"Action: {decision.get('action')}", indent=3)
        logger.bullet(f"Reasoning: {decision.get('reasoning', 'N/A')}", indent=3)
        logger.bullet(f"Confidence: {decision.get('confidence', 0.0)}", indent=3)
        if decision.get("tool_name"):
            logger.bullet(f"Tool: {decision['tool_name']}", indent=3)
    except Exception as e:
        logger.error(f"Failed to make decision: {e}", indent=2)
        import traceback

        traceback.print_exc()

    logger.rule(
        "5. Testing full query answering (requires initialized repository)",
        icon="ℹ️",
    )
    logger.warning(
        "This test requires a repository to be initialized first.",
        indent=1,
    )
    logger.warning(
        "Run the main application or test_pipeline.py to initialize.",
        indent=1,
    )

    logger.success("LLMAgent test completed!", icon="✅")
    logger.warning(
        "Some tests may warn if the database is empty — initialize a repository for full coverage.",
        indent=0,
    )


if __name__ == "__main__":
    test_agent()
