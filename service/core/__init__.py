"""
Orchestration of the entire core processing pipeline.
"""

from typing import Dict, Any
from core.parser import CodeParser
from core.summarizer import SummaryGenerator
from core.db_manager import DatabaseManager
from core.classifier import QueryClassifier
from core.retrieval import RetrievalEngine
from core.agent import LLMAgent
from utils.json_builder import (
    build_summary_id,
    extract_file_summary_id,
    extract_component_id_from_mapping,
)


class CodeUnderstandingPipeline:
    """
    Main entry point coordinating all core modules.
    """

    def __init__(self, repo_path: str, llm_client, db_session):
        """Initialize all components"""
        self.parser = CodeParser(repo_path)
        self.summarizer = SummaryGenerator(llm_client)
        self.db_manager = DatabaseManager(db_session)
        self.classifier = QueryClassifier(llm_client)
        self.retrieval = RetrievalEngine(self.db_manager)
        self.agent = LLMAgent(llm_client, self.db_manager)

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
        print("Initializing repository...")

        # Parse repository
        parsed_repo = self.parser.parse_repository()
        print(f"Parsed {len(parsed_repo['files'])} files")

        # Generate repository summary
        repo_summary = self.summarizer.generate_repository_summary(parsed_repo)
        repo_id = build_summary_id("repository", parsed_repo["repository"]["name"])

        self.db_manager.insert_summary(
            summary_id=repo_id,
            level="repository",
            text=repo_summary,
            token_count=len(repo_summary.split()),
            target_id=parsed_repo["repository"]["name"],
        )
        print("Repository summary generated")

        # Process files
        files_processed = 0
        components_processed = 0

        for file_meta in parsed_repo["files"]:
            filepath = file_meta["filepath"]
            file_id = extract_file_summary_id(filepath)

            # Generate file summary
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
            for func in file_meta.get("functions", []):
                func_id = extract_component_id_from_mapping(func["name"], "function")
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

                components_processed += 1

            # Process classes
            for cls in file_meta.get("classes", []):
                cls_id = extract_component_id_from_mapping(cls["name"], "class")
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

                components_processed += 1

            files_processed += 1

        # Store dependencies
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

        print("Initialization complete:")
        print(f"  - Files processed: {files_processed}")
        print(f"  - Components processed: {components_processed}")
        print(f"  - Dependencies stored: {dependencies_stored}")

        return {
            "files_processed": files_processed,
            "components_processed": components_processed,
            "dependencies_stored": dependencies_stored,
            "repository_name": parsed_repo["repository"]["name"],
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
        print(f"  🔍 Processing query: '{query}'")

        # Classify query
        print("  🎯 Step 1: Classifying query...")
        classification = self.classifier.classify_query(query)
        print(
            f"    → Type: {classification['type']} (confidence: {classification['confidence']})"
        )
        if classification.get("target"):
            print(f"    → Target: {classification['target']}")

        # Retrieve initial context
        print("  📚 Step 2: Retrieving initial context...")
        initial_context = self.retrieval.retrieve_context(classification)
        print(f"    → Context type: {initial_context.get('entry_point')}")
        print(f"    → Token count: {initial_context.get('token_count', 0)}")

        # Show what was retrieved
        if initial_context.get("repo_summary"):
            print(
                f"    → Repository summary: {initial_context['repo_summary'].text[:50]}..."
            )
        if initial_context.get("file_summaries"):
            print(
                f"    → File summaries: {len(initial_context['file_summaries'])} files"
            )
        if initial_context.get("component_summary"):
            print(f"    → Component: {initial_context['component_summary'].target_id}")
        if initial_context.get("search_results"):
            print(
                f"    → Search results: {len(initial_context['search_results'])} matches"
            )
        if initial_context.get("execution_path"):
            print(
                f"    → Execution path: {len(initial_context['execution_path'])} components"
            )

        # Get user knowledge (simplified for now)
        print("  👤 Step 3: Loading user knowledge...")
        user_knowledge = {"expertise_level": "intermediate", "concepts_learned": []}
        print(f"    → Expertise level: {user_knowledge['expertise_level']}")

        # Answer query using agent
        print("  🤖 Step 4: Agent reasoning and tool execution...")
        response = self.agent.answer_query(query, initial_context, user_knowledge)
        print(f"    → Tools used: {response['tools_used']}")
        print(f"    → Sources gathered: {len(response['sources'])}")

        # Update user knowledge (simplified)
        if response["new_concepts_learned"]:
            print(f"    → New concepts learned: {response['new_concepts_learned']}")

        print("  ✅ Query processing complete!")

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
