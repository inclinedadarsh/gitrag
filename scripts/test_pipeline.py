#!/usr/bin/env python3
"""
Test script for CodeUnderstandingPipeline functionality.
Tests the full pipeline: initialization and query answering.
"""

import os
import time
from openai import OpenAI
from app.db import create_db_and_tables, get_session
from core import CodeUnderstandingPipeline
from utils.tui_logger import TUILogger


def get_llm_client():
    """Get LLM client."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def test_pipeline():
    """Test the full CodeUnderstandingPipeline."""
    mode = os.getenv("MODE", "production")
    logger = TUILogger(mode=mode)
    logger.show_logo()
    logger.rule("Testing CodeUnderstandingPipeline", icon="[TEST]")

    logger.info("1. Setting up database...", icon="[DB]")
    try:
        create_db_and_tables()
        session = get_session()
        logger.success("Database setup complete", indent=1)
    except Exception as e:
        logger.error(f"Database setup failed: {e}", indent=1)
        return

    logger.info("2. Initializing LLM client...", icon="[LLM]")
    try:
        llm_client = get_llm_client()
        logger.success("LLM client initialized", indent=1)
    except Exception as e:
        logger.error(f"LLM client initialization failed: {e}", indent=1)
        return

    logger.info("3. Initializing pipeline...", icon="[CFG]")
    repo_url = "https://github.com/inclinedadarsh/inclinet"
    logger.bullet(f"Repository: {repo_url}", indent=1)

    try:
        pipeline = CodeUnderstandingPipeline(
            repo_path=repo_url,
            llm_client=llm_client,
            db_session=session,
            logger=logger,
        )
        logger.success("Pipeline initialized", indent=1)
    except Exception as e:
        logger.error(f"Pipeline initialization failed: {e}", indent=1)
        return

    logger.rule("4. Testing repository initialization...", icon="[PKG]")
    logger.warning(
        "This may take several minutes depending on repository size...",
        indent=1,
    )

    start_time = time.time()
    try:
        result = pipeline.initialize_repository()
        elapsed = time.time() - start_time

        logger.success("Repository initialized successfully!", indent=1)
        logger.table(
            "Initialization Metrics",
            [
                ("Time taken", f"{elapsed:.2f} seconds"),
                ("Files processed", result["files_processed"]),
                ("Components processed", result["components_processed"]),
                ("Dependencies stored", result["dependencies_stored"]),
                ("Repository", result["repository_name"]),
            ],
        )
    except Exception as e:
        logger.error(f"Repository initialization failed: {e}", indent=1)
        import traceback

        traceback.print_exc()
        return

    logger.rule("5. Testing query answering...", icon="[ASK]")

    test_queries = [
        "What does this project do?",
        "How does the loss function work?",
        "Where is the neural network defined?",
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info(f"Query {i}: {query}", icon="[Q]", indent=1)

        start_time = time.time()
        try:
            response = pipeline.answer_user_query(query)
            elapsed = time.time() - start_time

            logger.success(f"Query processed in {elapsed:.2f} seconds", indent=2)
            logger.bullet(
                f"Classification: {response['classification']['type']}", indent=3
            )
            logger.bullet(f"Confidence: {response['confidence']:.2f}", indent=3)
            logger.bullet(f"Tools used: {response['tools_used']}", indent=3)

            if response.get("sources"):
                logger.bullet(f"Sources: {len(response['sources'])}", indent=3)

            if response.get("new_concepts_learned"):
                logger.bullet(
                    f"New concepts: {', '.join(response['new_concepts_learned'])}",
                    indent=3,
                )

            logger.panel(
                "Answer (first 200 chars)",
                f"{response['answer'][:200]}...",
                style="green",
            )

        except Exception as e:
            logger.error(f"Query processing failed: {e}", indent=2)
            import traceback

            traceback.print_exc()

    logger.info("6. Testing pipeline statistics...", icon="[STATS]")
    try:
        stats = pipeline.get_pipeline_stats()
        logger.success("Pipeline stats retrieved", indent=1)
        for key, value in stats.items():
            logger.bullet(f"{key}: {value}", indent=2)
    except Exception as e:
        logger.error(f"Failed to get stats: {e}", indent=1)

    logger.success(
        "CodeUnderstandingPipeline test completed successfully!", icon="[OK]"
    )


if __name__ == "__main__":
    test_pipeline()
