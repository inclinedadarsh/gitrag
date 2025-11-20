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
from utils.tui_logger import TUILogger

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


def print_help(logger: TUILogger):
    """Render command palette."""
    commands = [
        ("/help", "Show this help message"),
        ("/reset", "Reset and initialize a new repository"),
        ("/exit or /quit", "Exit the application"),
    ]
    logger.help(commands)


def initialize_repository(
    pipeline: CodeUnderstandingPipeline, repo_url: str, logger: TUILogger
) -> bool:
    """Initialize repository with the provided URL."""
    import time

    logger.rule("Repository Initialization", icon="[INIT]")
    logger.info(f"Target repository: {repo_url}", icon="[URL]")
    logger.info(
        "This may take a few minutes depending on the repository size...",
        icon="[WAIT]",
    )

    start_time = time.time()

    try:
        with logger.status("Parsing and summarizing repository..."):
            result = pipeline.initialize_repository()
        elapsed_time = time.time() - start_time

        logger.success("Repository initialization complete!", icon="[DONE]")
        logger.table(
            "Initialization Summary",
            [
                ("Repository", result["repository_name"]),
                ("Files Processed", result["files_processed"]),
                ("Functions Processed", result.get("functions_processed", 0)),
                ("Classes Processed", result.get("classes_processed", 0)),
                ("Total Components", result["components_processed"]),
                ("Dependencies Stored", result["dependencies_stored"]),
                ("Time Taken", f"{elapsed_time:.2f}s"),
            ],
        )

        return True

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"Error initializing repository after {elapsed_time:.2f}s: {e}",
            icon="[ERR]",
        )

        # Check if it's a UNIQUE constraint error (database already has data)
        if "UNIQUE constraint" in str(e) or "IntegrityError" in str(type(e).__name__):
            logger.warning("Database already contains data for this repository.")
            logger.bullet("Use /reset to clear the database and start fresh.", indent=2)

        import traceback

        traceback.print_exc()
        return False


def process_query(
    pipeline: CodeUnderstandingPipeline, query: str, logger: TUILogger
) -> None:
    """Process a user query and display results."""
    import time

    logger.rule("Processing Query", icon="[QUERY]")
    logger.panel("User Question", query, style="cyan")

    start_time = time.time()

    try:
        response = pipeline.answer_user_query(query)
        elapsed_time = time.time() - start_time

        logger.panel("Answer", response["answer"], style="green")

        # Show metadata in a clean format
        logger.table(
            "Query Details",
            [
                ("Classification", response["classification"]["type"]),
                ("Confidence", f"{response.get('confidence', 0.0):.2f}"),
                ("Processing Time", f"{elapsed_time:.2f}s"),
                (
                    "Tools Used",
                    ", ".join(response["tools_used"])
                    if response.get("tools_used")
                    else "--",
                ),
            ],
        )

        if response.get("sources"):
            logger.info(f"Sources ({len(response['sources'])} total)", icon="[SRC]")
            for i, source in enumerate(response["sources"][:5], 1):
                logger.bullet(f"{i}. {source.target_id} ({source.level})", indent=2)
            if len(response["sources"]) > 5:
                logger.bullet(
                    f"... and {len(response['sources']) - 5} more",
                    indent=2,
                )

        if response.get("new_concepts_learned"):
            logger.info(
                f"New concepts learned: {', '.join(response['new_concepts_learned'])}",
                icon="[LEARN]",
            )

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"Error processing query after {elapsed_time:.2f}s: {e}",
            icon="[ERR]",
        )
        import traceback

        traceback.print_exc()


def main():
    """Main application loop."""
    mode = os.getenv("MODE", "production").strip().lower()
    logger = TUILogger(mode=mode)

    logger.show_logo()
    logger.rule("GitRAG - Terminal Knowledge Workbench", icon="[APP]")
    logger.info(f"MODE={mode}", icon="[MODE]")

    # Setup database
    logger.info("Setting up database...", icon="[DB]")
    try:
        create_db_and_tables()
        logger.success("Database initialized")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)

    # Initialize LLM client
    logger.info("Initializing LLM client...", icon="[LLM]")
    try:
        llm_client = get_llm_client()
        logger.success("LLM client initialized")
    except Exception as e:
        logger.error(f"LLM client initialization failed: {e}")
        sys.exit(1)

    # Get database session
    session = get_session()

    # Initialize pipeline (will be set up with repo later)
    pipeline: Optional[CodeUnderstandingPipeline] = None

    logger.success("Setup complete! Ready to initialize a repository.", icon="[READY]")
    print_help(logger)

    # Main loop
    initialized = False

    while True:
        try:
            if not initialized:
                # Need to initialize repository first
                logger.rule("Repository Initialization Required", icon="[INIT]")
                logger.bullet(
                    "Enter a GitHub repository URL to analyze.",
                    indent=0,
                    icon="[TIP]",
                )
                logger.bullet(
                    "Example: https://github.com/username/repository", indent=1
                )

                repo_url = input("\nRepository URL (or /help for commands): ").strip()

                if repo_url in ["/help", "/h"]:
                    print_help(logger)
                    continue
                elif repo_url in ["/exit", "/quit", "/q"]:
                    logger.info("Goodbye!", icon="[BYE]")
                    break
                elif not repo_url:
                    continue

                if not (
                    repo_url.startswith("http://") or repo_url.startswith("https://")
                ):
                    logger.error("Invalid URL. Please provide a full GitHub URL.")
                    continue

                # Initialize pipeline with repository
                pipeline = CodeUnderstandingPipeline(
                    repo_path=repo_url,
                    llm_client=llm_client,
                    db_session=session,
                    logger=logger,
                )

                if initialize_repository(pipeline, repo_url, logger):
                    initialized = True
                    logger.rule("Ready for Questions!", icon="[READY]")
                    logger.info(
                        "You can now ask questions about the codebase!", icon="[ASK]"
                    )
                    logger.bullet("Type /help for commands or /exit to quit.", indent=1)
                else:
                    pipeline = None
                    continue
            else:
                # Ready for queries
                query = input("\nAsk a question (or /help for commands): ").strip()

                if not query:
                    continue

                if query in ["/help", "/h"]:
                    print_help(logger)
                    continue
                elif query in ["/reset", "/r"]:
                    logger.info("Resetting database...", icon="[RESET]")
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
                        logger.success(
                            "Database cleared. Please initialize a new repository.",
                            icon="[OK]",
                        )
                    except Exception as e:
                        logger.error(f"Error resetting database: {e}", icon="[ERR]")
                        logger.bullet(
                            "You may need to delete database.db manually.",
                            indent=1,
                            icon="[TIP]",
                        )
                    continue
                elif query in ["/exit", "/quit", "/q"]:
                    logger.info("Goodbye!", icon="[BYE]")
                    break
                else:
                    process_query(pipeline, query, logger)

        except KeyboardInterrupt:
            logger.info("Exiting. Goodbye!", icon="[BYE]")
            break
        except EOFError:
            logger.info("Exiting. Goodbye!", icon="[BYE]")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}", icon="[ERR]")
            import traceback

            traceback.print_exc()

    # Cleanup
    if session:
        session.close()


if __name__ == "__main__":
    main()
