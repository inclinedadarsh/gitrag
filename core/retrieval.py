"""
Retrieval engine for executing database queries based on classification results.
"""

from typing import Dict, List, Any
from core.db_manager import DatabaseManager
from models import Summary


class RetrievalEngine:
    """
    Retrieves context from database based on classification.

    Attributes:
        db_manager: DatabaseManager instance
        max_context_tokens: Limit total tokens returned
    """

    def __init__(
        self, db_manager: DatabaseManager, max_context_tokens: int = 4000
    ) -> None:
        """Initialize with database manager and token limit"""
        self.db_manager = db_manager
        self.max_context_tokens = max_context_tokens

    def retrieve_context(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: retrieves appropriate context based on classification.

        Args:
            classification: Output from QueryClassifier
            {
                "type": "component_specific",
                "entry_point": "component",
                "target": "authenticate_user",
                "retrieval_strategy": "focused"
            }

        Returns:
        {
            "summaries": [Summary objects],
            "metadata": {...},
            "token_count": 1250,
            "entry_point": "component"
        }
        """
        entry_point = classification.get("entry_point", "repository")
        target = classification.get("target")

        # Route based on entry_point
        if entry_point == "repository":
            return self.retrieve_repository_overview()
        elif entry_point == "component":
            if target:
                return self.retrieve_component_context(target)
            else:
                return self.retrieve_by_search("component")
        elif entry_point == "dependency_graph":
            if target:
                return self.retrieve_execution_trace(target)
            else:
                return self.retrieve_dependency_graph()
        elif entry_point == "search":
            if target:
                return self.retrieve_by_search(target)
            else:
                return self.retrieve_by_search("general")
        else:
            # Fallback to repository overview
            return self.retrieve_repository_overview()

    def retrieve_repository_overview(self) -> Dict[str, Any]:
        """
        Retrieve repository-level summary.

        Returns:
        {
            "repo_summary": Summary object,
            "file_summaries": [compact summaries for top files],
            "architecture": "explanation of structure",
            "token_count": 800
        }
        """
        # Get repository summary
        repo_summary = self.db_manager.get_repository_summary()

        # Get file summaries (limit to top files to stay within token limit)
        file_summaries = self.db_manager.get_all_summaries_by_level("file")

        # Limit file summaries to prevent token overflow
        max_files = min(10, len(file_summaries))
        file_summaries = file_summaries[:max_files]

        # Build architecture explanation
        architecture = self._build_architecture_summary(file_summaries)

        # Calculate token count
        token_count = 0
        if repo_summary:
            token_count += repo_summary.token_count
        for file_summary in file_summaries:
            token_count += file_summary.token_count

        return {
            "repo_summary": repo_summary,
            "file_summaries": file_summaries,
            "architecture": architecture,
            "token_count": token_count,
            "entry_point": "repository",
        }

    def retrieve_component_context(self, component_name: str) -> Dict[str, Any]:
        """
        Retrieve context for a specific component.

        Args:
            component_name: "authenticate_user"

        Returns:
        {
            "component_summary": Summary,
            "code_location": CodeMapping,
            "parent_file_summary": Summary,
            "dependencies": [summaries of called functions],
            "dependents": [summaries of functions that call this],
            "token_count": 2000
        }
        """
        # Find component summary by name
        component_summary = self.db_manager.search_by_component_name(component_name)

        if not component_summary:
            return {
                "component_summary": None,
                "code_location": None,
                "parent_file_summary": None,
                "dependencies": [],
                "dependents": [],
                "token_count": 0,
                "entry_point": "component",
                "error": f"Component '{component_name}' not found",
            }

        # Get code location and parent file context
        component_with_code = self.db_manager.get_component_summary_with_code(
            component_summary.id
        )
        code_location = (
            component_with_code.get("code_mapping") if component_with_code else None
        )

        # Get parent file summary
        parent_file_summary = None
        if component_with_code and component_with_code.get("code_mapping"):
            filepath = component_with_code["code_mapping"].filepath
            parent_file_summary = self.db_manager.get_file_summary(filepath)

        # Get dependencies (what this component calls)
        dependencies = self.db_manager.get_dependencies_of_component(
            component_summary.id, "calls"
        )

        # Get dependents (what calls this component)
        dependents = self.db_manager.get_dependents_of_component(
            component_summary.id, "calls"
        )

        # Calculate token count
        token_count = component_summary.token_count
        if parent_file_summary:
            token_count += parent_file_summary.token_count
        for dep in dependencies:
            token_count += dep.token_count
        for dep in dependents:
            token_count += dep.token_count

        return {
            "component_summary": component_summary,
            "code_location": code_location,
            "parent_file_summary": parent_file_summary,
            "dependencies": dependencies,
            "dependents": dependents,
            "token_count": token_count,
            "entry_point": "component",
        }

    def retrieve_execution_trace(
        self, start_component: str, max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Trace execution flow starting from a component.

        Args:
            start_component: "func_login_endpoint"
            max_depth: How deep to follow the chain

        Returns:
        {
            "execution_path": [
                {"summary": Summary, "depth": 0},
                {"summary": Summary, "depth": 1},
                ...
            ],
            "call_chain": "func_login -> authenticate_user -> check_password",
            "token_count": 3000
        }
        """
        # Find the start component
        start_summary = self.db_manager.search_by_component_name(start_component)

        if not start_summary:
            # Fallback: search for similar components
            fallback_results = self.db_manager.search_summaries_by_keyword(
                start_component, limit=5
            )
            if fallback_results:
                # Use the first result as start component
                start_summary = fallback_results[0]
            else:
                return {
                    "execution_path": [],
                    "call_chain": "",
                    "token_count": 0,
                    "entry_point": "dependency_graph",
                    "error": f"Start component '{start_component}' not found",
                    "fallback_suggestions": [s.target_id for s in fallback_results[:3]],
                }

        # Trace execution path
        execution_path = self.db_manager.trace_execution_path(
            start_summary.id, max_depth
        )

        # If no execution path found, try to find related components
        if not execution_path:
            # Search for components that might be related
            related_search = self.db_manager.search_summaries_by_keyword(
                start_component, limit=10
            )
            execution_path = related_search[:max_depth]

        # Build execution path with depth information
        path_with_depth = []
        current_depth = 0
        for summary in execution_path:
            path_with_depth.append({"summary": summary, "depth": current_depth})
            current_depth += 1

        # Build call chain representation
        call_chain = " -> ".join([s["summary"].target_id for s in path_with_depth])

        # Calculate token count
        token_count = sum(s["summary"].token_count for s in path_with_depth)

        return {
            "execution_path": path_with_depth,
            "call_chain": call_chain,
            "token_count": token_count,
            "entry_point": "dependency_graph",
        }

    def retrieve_dependency_graph(self) -> Dict[str, Any]:
        """
        Retrieve the complete dependency graph.

        Returns:
        {
            "dependency_graph": {source_id: [target_ids]},
            "graph_summary": "explanation of relationships",
            "token_count": 500
        }
        """
        # Get complete dependency graph
        dependency_graph = self.db_manager.get_dependency_graph()

        # Build graph summary
        graph_summary = self._build_graph_summary(dependency_graph)

        return {
            "dependency_graph": dependency_graph,
            "graph_summary": graph_summary,
            "token_count": 500,  # Fixed estimate for graph structure
            "entry_point": "dependency_graph",
        }

    def retrieve_by_search(self, keyword: str) -> Dict[str, Any]:
        """
        Search for components matching keyword.

        Args:
            keyword: "authentication" or "password"

        Returns:
        {
            "search_results": [
                {"summary": Summary, "relevance": 0.95},
                {"summary": Summary, "relevance": 0.87},
                ...
            ],
            "total_matches": 12,
            "token_count": 1500
        }
        """
        # Search summaries for keyword matches
        search_results = self.db_manager.search_summaries_by_keyword(keyword, limit=20)

        # Calculate relevance scores (simple keyword frequency for now)
        results_with_relevance = []
        for summary in search_results:
            relevance = self._calculate_relevance(summary, keyword)
            results_with_relevance.append({"summary": summary, "relevance": relevance})

        # Sort by relevance
        results_with_relevance.sort(key=lambda x: x["relevance"], reverse=True)

        # Limit results to stay within token budget
        limited_results = results_with_relevance[:10]

        # Calculate token count
        token_count = sum(r["summary"].token_count for r in limited_results)

        return {
            "search_results": limited_results,
            "total_matches": len(search_results),
            "token_count": token_count,
            "entry_point": "search",
        }

    def _build_architecture_summary(self, file_summaries: List[Summary]) -> str:
        """
        Build a high-level architecture explanation from file summaries.
        """
        if not file_summaries:
            return "No file information available."

        # Group files by directory/type
        directories = {}
        for file_summary in file_summaries:
            # Extract directory from target_id (filepath)
            filepath = file_summary.target_id
            if "/" in filepath:
                directory = filepath.split("/")[0]
            else:
                directory = "root"

            if directory not in directories:
                directories[directory] = []
            directories[directory].append(file_summary)

        # Build architecture description
        architecture_parts = []
        for directory, files in directories.items():
            architecture_parts.append(f"{directory}/: {len(files)} files")

        return f"Project structure: {', '.join(architecture_parts)}"

    def _build_graph_summary(self, dependency_graph: Dict[str, List[str]]) -> str:
        """
        Build a summary of the dependency graph.
        """
        if not dependency_graph:
            return "No dependencies found."

        total_relationships = sum(len(targets) for targets in dependency_graph.values())
        most_connected = (
            max(dependency_graph.items(), key=lambda x: len(x[1]))
            if dependency_graph
            else None
        )

        summary = f"Found {total_relationships} dependency relationships across {len(dependency_graph)} components."

        if most_connected:
            summary += f" Most connected component: {most_connected[0]} ({len(most_connected[1])} dependencies)."

        return summary

    def _calculate_relevance(self, summary: Summary, keyword: str) -> float:
        """
        Calculate relevance score for a summary based on keyword.
        """
        text = summary.text.lower()
        keyword_lower = keyword.lower()

        # Simple frequency-based relevance
        keyword_count = text.count(keyword_lower)
        total_words = len(text.split())

        if total_words == 0:
            return 0.0

        # Base relevance on keyword frequency
        frequency_score = keyword_count / total_words

        # Boost score if keyword appears in target_id
        if keyword_lower in summary.target_id.lower():
            frequency_score += 0.2

        # Boost score if keyword appears in level (function, class, etc.)
        if keyword_lower in summary.level.lower():
            frequency_score += 0.1

        return min(frequency_score, 1.0)  # Cap at 1.0

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retrieval engine.

        Returns:
        {
            "total_summaries": 150,
            "repository_summaries": 1,
            "file_summaries": 25,
            "function_summaries": 100,
            "class_summaries": 24,
            "total_dependencies": 45
        }
        """
        # Get counts by level
        repo_count = len(self.db_manager.get_all_summaries_by_level("repository"))
        file_count = len(self.db_manager.get_all_summaries_by_level("file"))
        func_count = len(self.db_manager.get_all_summaries_by_level("function"))
        class_count = len(self.db_manager.get_all_summaries_by_level("class"))

        # Get dependency count
        dependency_graph = self.db_manager.get_dependency_graph()
        total_dependencies = sum(len(targets) for targets in dependency_graph.values())

        return {
            "total_summaries": repo_count + file_count + func_count + class_count,
            "repository_summaries": repo_count,
            "file_summaries": file_count,
            "function_summaries": func_count,
            "class_summaries": class_count,
            "total_dependencies": total_dependencies,
        }
