"""
Orchestration of the entire core processing pipeline.
"""

from typing import Any, Dict, Optional
from core.agent import LLMAgent
from core.classifier import QueryClassifier
from core.db_manager import DatabaseManager
from core.parser import CodeParser
from core.retrieval import RetrievalEngine
from core.summarizer import SummaryGenerator
from utils.json_builder import (
    build_summary_id,
    extract_component_id_from_mapping,
    extract_file_summary_id,
)
from utils.tui_logger import TUILogger


class CodeUnderstandingPipeline:
    """
    Main entry point coordinating all core modules.
    """

    def __init__(
        self,
        repo_path: str,
        llm_client,
        db_session,
        logger: Optional[TUILogger] = None,
    ):
        """Initialize all components"""
        self.parser = CodeParser(repo_path)
        self.summarizer = SummaryGenerator(llm_client)
        self.db_manager = DatabaseManager(db_session)
        self.classifier = QueryClassifier(llm_client)
        self.retrieval = RetrievalEngine(self.db_manager)
        self.logger = logger or TUILogger()
        self.agent = LLMAgent(llm_client, self.db_manager, logger=self.logger)

    def initialize_repository(self) -> Dict[str, Any]:
        """
        One-time setup: parse repo and generate summaries.

        Process:
        1. parsed = parser.parse_repository()
        2. For repo: summarizer.generate_repository_summary()
        3. For each file: summarizer.generate_file_summary_compact()
        4. For each component: summarizer.generate_component_summary()
        5. Insert all into database via db_manager
        6. Build dependency graph
        """
        self.logger.info("Step 1: Parsing repository...", icon="📦")

        # Parse repository
        parsed_repo = self.parser.parse_repository()
        total_files = len(parsed_repo["files"])
        self.logger.success(f"Parsed {total_files} files", indent=1)

        # Generate repository summary
        self.logger.info("Step 2: Generating repository summary...", icon="📝")
        repo_summary = self.summarizer.generate_repository_summary(parsed_repo)
        repo_id = build_summary_id("repository", parsed_repo["repository"]["name"])

        self.db_manager.insert_summary(
            summary_id=repo_id,
            level="repository",
            text=repo_summary,
            token_count=len(repo_summary.split()),
            target_id=parsed_repo["repository"]["name"],
        )
        self.logger.success("Repository summary generated", indent=1)

        # Process files
        self.logger.info(f"Step 3: Processing {total_files} files...", icon="📄")
        files_processed = 0
        components_processed = 0
        functions_processed = 0
        classes_processed = 0

        for file_idx, file_meta in enumerate(parsed_repo["files"], 1):
            filepath = file_meta["filepath"]
            file_id = extract_file_summary_id(filepath)

            # Generate file summary
            if self.logger.is_dev:
                self.logger.bullet(
                    f"[{file_idx}/{total_files}] Processing file: {filepath}",
                    indent=1,
                )
            file_summary = self.summarizer.generate_file_summary_compact(file_meta)

            self.db_manager.insert_summary(
                summary_id=file_id,
                level="file",
                text=file_summary,
                token_count=len(file_summary.split()),
                parent_id=repo_id,
                target_id=filepath,
            )

            # Store code mapping
            self.db_manager.insert_code_mapping(
                summary_id=file_id,
                filepath=filepath,
                line_start=1,
                line_end=100,  # Approximate
                element_type="file",
                content_preview=f"File: {filepath}",
            )

            # Process functions
            functions = file_meta.get("functions", [])
            if functions and self.logger.is_dev:
                self.logger.bullet(
                    f"Generating {len(functions)} function summaries",
                    indent=2,
                    icon="ƒ",
                )
            for func in functions:
                func_id = extract_component_id_from_mapping(
                    func["name"], "function", filepath, func.get("line_start")
                )
                if self.logger.is_dev:
                    self.logger.bullet(f"Function: {func['name']}", indent=3)
                func_summary = self.summarizer.generate_component_summary(
                    func, "function"
                )

                self.db_manager.insert_summary(
                    summary_id=func_id,
                    level="function",
                    text=func_summary,
                    token_count=len(func_summary.split()),
                    parent_id=file_id,
                    target_id=func["name"],
                )

                # Store code mapping for function
                if func.get("line_start") and func.get("line_end"):
                    self.db_manager.insert_code_mapping(
                        summary_id=func_id,
                        filepath=filepath,
                        line_start=func["line_start"],
                        line_end=func["line_end"],
                        element_type="function",
                        content_preview=func.get("signature", func["name"]),
                    )

                functions_processed += 1
                components_processed += 1

            # Process classes
            classes = file_meta.get("classes", [])
            if classes and self.logger.is_dev:
                self.logger.bullet(
                    f"Generating {len(classes)} class summaries",
                    indent=2,
                    icon="🏛️",
                )
            for cls in classes:
                cls_id = extract_component_id_from_mapping(
                    cls["name"], "class", filepath, cls.get("line_start")
                )
                if self.logger.is_dev:
                    self.logger.bullet(f"Class: {cls['name']}", indent=3)
                cls_summary = self.summarizer.generate_component_summary(cls, "class")

                self.db_manager.insert_summary(
                    summary_id=cls_id,
                    level="class",
                    text=cls_summary,
                    token_count=len(cls_summary.split()),
                    parent_id=file_id,
                    target_id=cls["name"],
                )

                # Store code mapping for class
                if cls.get("line_start") and cls.get("line_end"):
                    self.db_manager.insert_code_mapping(
                        summary_id=cls_id,
                        filepath=filepath,
                        line_start=cls["line_start"],
                        line_end=cls["line_end"],
                        element_type="class",
                        content_preview=cls["name"],
                    )

                classes_processed += 1
                components_processed += 1

            files_processed += 1

        # Store dependencies
        self.logger.info("Step 4: Storing dependencies...", icon="🔗")
        dependency_graph = parsed_repo.get("dependency_graph", {})
        dependencies_stored = 0

        for source_file, target_files in dependency_graph.items():
            source_file_id = extract_file_summary_id(source_file)

            for target_file in target_files:
                if not target_file.endswith(".py"):
                    # External dependency
                    target_id = f"external_{target_file}"
                else:
                    # Internal file dependency
                    target_id = extract_file_summary_id(target_file)

                self.db_manager.insert_dependency(
                    source_id=source_file_id,
                    target_id=target_id,
                    relationship="imports",
                )
                dependencies_stored += 1

        self.logger.success(f"Stored {dependencies_stored} dependencies", indent=1)

        return {
            "files_processed": files_processed,
            "components_processed": components_processed,
            "dependencies_stored": dependencies_stored,
            "repository_name": parsed_repo["repository"]["name"],
            "functions_processed": functions_processed,
            "classes_processed": classes_processed,
        }

    def answer_user_query(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Main query-answering flow.

        Process:
        1. classification = classifier.classify_query(query)
        2. initial_context = retrieval.retrieve_context(classification)
        3. user_knowledge = db_manager.get_user_knowledge(user_id)
        4. response = agent.answer_query(query, initial_context, user_knowledge)
        5. Update user_knowledge with learned concepts
        6. Return response
        """
        self.logger.info(f"Processing query: '{query}'", icon="🔍")

        # Classify query
        self.logger.bullet("Step 1: Classifying query...", indent=1, icon="🎯")
        classification = self.classifier.classify_query(query)
        self.logger.bullet(
            f"Type: {classification['type']} (confidence: {classification['confidence']:.2f})",
            indent=2,
        )
        if classification.get("target"):
            self.logger.bullet(f"Target: {classification['target']}", indent=2)
        if self.logger.is_dev:
            self.logger.dev("Classification Payload", classification)

        # Retrieve initial context
        self.logger.bullet("Step 2: Retrieving initial context...", indent=1, icon="📚")
        initial_context = self.retrieval.retrieve_context(classification)
        self.logger.bullet(
            f"Context type: {initial_context.get('entry_point', '—')}", indent=2
        )
        self.logger.bullet(
            f"Token count: {initial_context.get('token_count', 0)}", indent=2
        )

        if self.logger.is_dev:
            context_snapshot = {
                "repo_summary": bool(initial_context.get("repo_summary")),
                "file_summaries": len(initial_context.get("file_summaries", [])),
                "component_summary": initial_context.get("component_summary").target_id
                if initial_context.get("component_summary")
                else None,
                "search_results": len(initial_context.get("search_results", [])),
                "execution_path": len(initial_context.get("execution_path", [])),
            }
            self.logger.dev("Context Snapshot", context_snapshot)

        # Get user knowledge (simplified for now)
        self.logger.bullet("Step 3: Loading user knowledge...", indent=1, icon="👤")
        user_knowledge = {"expertise_level": "intermediate", "concepts_learned": []}
        self.logger.bullet(
            f"Expertise level: {user_knowledge['expertise_level']}", indent=2
        )

        # Answer query using agent
        self.logger.bullet(
            "Step 4: Agent reasoning and tool execution...", indent=1, icon="🤖"
        )
        response = self.agent.answer_query(query, initial_context, user_knowledge)
        self.logger.bullet(
            f"Tools used: {', '.join(response['tools_used']) if response['tools_used'] else '—'}",
            indent=2,
        )
        self.logger.bullet(f"Sources gathered: {len(response['sources'])}", indent=2)

        # Update user knowledge (simplified)
        if response["new_concepts_learned"]:
            self.logger.bullet(
                f"New concepts learned: {response['new_concepts_learned']}", indent=2
            )

        self.logger.success("Query processing complete!", icon="✅", indent=1)

        return {
            "query": query,
            "classification": classification,
            "answer": response["answer"],
            "sources": response["sources"],
            "tools_used": response["tools_used"],
            "new_concepts_learned": response["new_concepts_learned"],
            "confidence": response["confidence"],
        }

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get statistics about the pipeline state."""
        return self.retrieval.get_retrieval_stats()

    def reset_user_knowledge(self, user_id: str) -> bool:
        """Reset user knowledge for a specific user."""
        # This would implement user knowledge reset
        # For now, just return True
        return True
