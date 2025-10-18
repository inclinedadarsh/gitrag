"""
Database operations for summaries, code mappings, and dependencies.
"""

from typing import Any, Dict, List, Optional
from sqlmodel import Session, select, and_, or_
from models import Summary, CodeMapping, Dependency


class DatabaseManager:
    """
    Manages all database operations.

    Attributes:
        session: SQLModel session
    """

    def __init__(self, session: Session) -> None:
        """Initialize with database session"""
        self.session = session

    # ========== INSERT OPERATIONS ==========

    def insert_summary(
        self,
        summary_id: str,
        level: str,
        text: str,
        token_count: int,
        parent_id: Optional[str] = None,
        summary_type: Optional[str] = None,
        target_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Summary:
        """
        Insert a summary into database.

        Args:
            summary_id: Unique ID (e.g., "func_authenticate_user")
            level: "repository" | "file" | "function" | "class"
            text: The actual summary text
            token_count: Number of tokens
            parent_id: Parent component ID if hierarchical
            summary_type: "compact" | "full" for file-level
            target_id: What this summarizes (defaults to summary_id)
            metadata: Additional JSON data

        Process:
        1. Create Summary object
        2. Add to session
        3. Commit
        4. Return created object
        """
        if target_id is None:
            target_id = summary_id

        summary = Summary(
            id=summary_id,
            level=level,
            type=summary_type,
            target_id=target_id,
            text=text,
            token_count=token_count,
            parent_id=parent_id,
            metadata_=metadata,
        )

        self.session.add(summary)
        self.session.commit()
        self.session.refresh(summary)
        return summary

    def insert_code_mapping(
        self,
        summary_id: str,
        filepath: str,
        line_start: int,
        line_end: int,
        element_type: str,
        content_preview: Optional[str] = None,
    ) -> CodeMapping:
        """
        Insert mapping from summary to source code location.

        Process:
        1. Create CodeMapping object
        2. Add to session
        3. Commit
        """
        mapping = CodeMapping(
            summary_id=summary_id,
            filepath=filepath,
            line_start=line_start,
            line_end=line_end,
            element_type=element_type,
            content_preview=content_preview,
        )

        self.session.add(mapping)
        self.session.commit()
        self.session.refresh(mapping)
        return mapping

    def insert_dependency(
        self, source_id: str, target_id: str, relationship: str
    ) -> Dependency:
        """
        Insert dependency relationship between components.

        Args:
            source_id: Component that calls/imports
            target_id: Component being called/imported
            relationship: "calls" | "imports" | "inherits" | "contains"

        Process:
        1. Create Dependency object
        2. Add to session
        3. Commit
        """
        dependency = Dependency(
            source_id=source_id, target_id=target_id, relationship=relationship
        )

        self.session.add(dependency)
        self.session.commit()
        self.session.refresh(dependency)
        return dependency

    def bulk_insert_summaries(
        self, summaries_list: List[Dict[str, Any]]
    ) -> List[Summary]:
        """
        Insert multiple summaries at once (for efficiency).

        Args:
            summaries_list: List of {id, level, text, token_count, ...}

        Process:
        1. Create Summary objects for each
        2. Add all to session
        3. Single commit
        """
        summaries = []
        for data in summaries_list:
            summary = Summary(
                id=data["id"],
                level=data["level"],
                type=data.get("type"),
                target_id=data.get("target_id", data["id"]),
                text=data["text"],
                token_count=data["token_count"],
                parent_id=data.get("parent_id"),
                metadata_=data.get("metadata"),
            )
            summaries.append(summary)
            self.session.add(summary)

        self.session.commit()
        for summary in summaries:
            self.session.refresh(summary)
        return summaries

    # ========== QUERY OPERATIONS ==========

    def get_repository_summary(self) -> Optional[Summary]:
        """
        Get the repository-level summary.

        Process:
        1. Query: SELECT * FROM Summary WHERE level='repository'
        2. Return first result
        """
        statement = select(Summary).where(Summary.level == "repository")
        return self.session.exec(statement).first()

    def get_file_summary(
        self, filepath: str, summary_type: str = "compact"
    ) -> Optional[Summary]:
        """
        Get file summary (compact or full).

        Args:
            filepath: "auth/login.py"
            summary_type: "compact" | "full"

        Process:
        1. Query CodeMapping to find summary_id for this filepath
        2. Query: SELECT * FROM Summary WHERE id=summary_id AND type=summary_type
        3. Return result
        """
        # First find summary_id from CodeMapping
        mapping_stmt = select(CodeMapping).where(CodeMapping.filepath == filepath)
        mapping = self.session.exec(mapping_stmt).first()

        if not mapping:
            return None

        # Then get the summary
        summary_stmt = select(Summary).where(
            and_(Summary.id == mapping.summary_id, Summary.type == summary_type)
        )
        return self.session.exec(summary_stmt).first()

    def get_component_summary(self, component_name: str) -> Optional[Summary]:
        """
        Get summary for a function/class/section by name.

        Args:
            component_name: "authenticate_user" or "AuthManager"

        Process:
        1. Query CodeMapping WHERE content contains component_name
           (or use fuzzy search)
        2. Get matching summary_id
        3. Query Summary WHERE id=summary_id
        4. Return result
        """
        # Search in CodeMapping by content_preview
        mapping_stmt = select(CodeMapping).where(
            CodeMapping.content_preview.like(f"%{component_name}%")
        )
        mapping = self.session.exec(mapping_stmt).first()

        if not mapping:
            return None

        # Get the summary
        summary_stmt = select(Summary).where(Summary.id == mapping.summary_id)
        return self.session.exec(summary_stmt).first()

    def get_file_summaries_for_directory(self, directory: str) -> List[Summary]:
        """
        Get all file summaries in a directory.

        Args:
            directory: "auth/" or "database/"

        Process:
        1. Query CodeMapping WHERE filepath LIKE "auth/%"
        2. Get all summary_ids
        3. Query Summary WHERE id IN (summary_ids)
        4. Return all results
        """
        # Find all mappings for files in directory
        mapping_stmt = select(CodeMapping).where(
            CodeMapping.filepath.like(f"{directory}%")
        )
        mappings = self.session.exec(mapping_stmt).all()

        if not mappings:
            return []

        summary_ids = [m.summary_id for m in mappings]

        # Get all summaries
        summary_stmt = select(Summary).where(Summary.id.in_(summary_ids))
        return list(self.session.exec(summary_stmt).all())

    def get_component_summary_with_code(
        self, summary_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get summary AND code location together.

        Returns:
        {
            "summary": Summary object,
            "code_mapping": CodeMapping object,
            "code_lines": (start, end)
        }

        Process:
        1. Query Summary WHERE id=summary_id
        2. Query CodeMapping WHERE summary_id=summary_id
        3. Return both
        """
        # Get summary
        summary_stmt = select(Summary).where(Summary.id == summary_id)
        summary = self.session.exec(summary_stmt).first()

        if not summary:
            return None

        # Get code mapping
        mapping_stmt = select(CodeMapping).where(CodeMapping.summary_id == summary_id)
        mapping = self.session.exec(mapping_stmt).first()

        if not mapping:
            return {"summary": summary, "code_mapping": None, "code_lines": None}

        return {
            "summary": summary,
            "code_mapping": mapping,
            "code_lines": (mapping.line_start, mapping.line_end),
        }

    # ========== DEPENDENCY QUERIES ==========

    def get_dependencies_of_component(
        self, summary_id: str, relationship: str
    ) -> List[Summary]:
        """
        Get all components that a target depends on.

        Args:
            summary_id: "func_authenticate_user"
            relationship: "calls" | "imports"

        Returns:
        List of Summary objects that this component calls/imports

        Example:
            get_dependencies_of_component("func_authenticate_user", "calls")
            → [Summary(id="func_check_password"), Summary(id="func_query_db")]

        Process:
        1. Query: SELECT target_id FROM Dependency
                  WHERE source_id=summary_id AND relationship=relationship
        2. For each target_id, get its Summary
        3. Return list of Summaries
        """
        # Get dependencies
        dep_stmt = select(Dependency).where(
            and_(
                Dependency.source_id == summary_id,
                Dependency.relationship == relationship,
            )
        )
        dependencies = self.session.exec(dep_stmt).all()

        if not dependencies:
            return []

        target_ids = [d.target_id for d in dependencies]

        # Get summaries for target components
        summary_stmt = select(Summary).where(Summary.id.in_(target_ids))
        return list(self.session.exec(summary_stmt).all())

    def get_dependents_of_component(
        self, summary_id: str, relationship: str
    ) -> List[Summary]:
        """
        Get all components that call/depend on target.

        Args:
            summary_id: "func_check_password"
            relationship: "calls"

        Returns:
        List of components that call check_password

        Process:
        1. Query: SELECT source_id FROM Dependency
                  WHERE target_id=summary_id AND relationship=relationship
        2. Get Summary for each source_id
        3. Return list
        """
        # Get dependents
        dep_stmt = select(Dependency).where(
            and_(
                Dependency.target_id == summary_id,
                Dependency.relationship == relationship,
            )
        )
        dependencies = self.session.exec(dep_stmt).all()

        if not dependencies:
            return []

        source_ids = [d.source_id for d in dependencies]

        # Get summaries for source components
        summary_stmt = select(Summary).where(Summary.id.in_(source_ids))
        return list(self.session.exec(summary_stmt).all())

    def trace_execution_path(
        self, start_component_id: str, max_depth: int = 3
    ) -> List[Summary]:
        """
        Follow the call chain starting from a component.

        Args:
            start_component_id: "func_login_endpoint"
            max_depth: How deep to follow the chain

        Returns:
        List of components in execution order:
        [func_login_endpoint → authenticate_user → check_password_hash → ...]

        Process:
        1. Start with start_component_id
        2. Find all components it calls (Dependency with relationship="calls")
        3. For each, recursively find what they call (up to max_depth)
        4. Build list maintaining order
        5. Return flattened list
        """
        visited = set()
        execution_path = []

        def trace_recursive(component_id: str, current_depth: int):
            if current_depth >= max_depth or component_id in visited:
                return

            visited.add(component_id)

            # Get the component summary
            summary_stmt = select(Summary).where(Summary.id == component_id)
            summary = self.session.exec(summary_stmt).first()
            if summary:
                execution_path.append(summary)

            # Find what this component calls
            dep_stmt = select(Dependency).where(
                and_(
                    Dependency.source_id == component_id,
                    Dependency.relationship == "calls",
                )
            )
            dependencies = self.session.exec(dep_stmt).all()

            # Recursively trace each called component
            for dep in dependencies:
                trace_recursive(dep.target_id, current_depth + 1)

        trace_recursive(start_component_id, 0)
        return execution_path

    # ========== SEARCH OPERATIONS ==========

    def search_summaries_by_keyword(
        self, keyword: str, limit: int = 10
    ) -> List[Summary]:
        """
        Find summaries containing a keyword.

        Args:
            keyword: "authentication" or "password"
            limit: Max results to return

        Returns:
        List of Summary objects matching keyword

        Process:
        1. Query: SELECT * FROM Summary WHERE text LIKE "%keyword%"
        2. Limit to top 10 matches (by relevance if possible)
        3. Return list
        """
        statement = (
            select(Summary).where(Summary.text.like(f"%{keyword}%")).limit(limit)
        )
        return list(self.session.exec(statement).all())

    def search_by_component_name(self, name: str) -> Optional[Summary]:
        """
        Find a specific component by name.

        Uses multiple search strategies for better matching.
        """
        # Strategy 1: Search by target_id (exact match)
        summary_stmt = select(Summary).where(Summary.target_id == name)
        summary = self.session.exec(summary_stmt).first()
        if summary:
            return summary

        # Strategy 2: Search by target_id (contains match)
        summary_stmt = select(Summary).where(Summary.target_id.like(f"%{name}%"))
        summary = self.session.exec(summary_stmt).first()
        if summary:
            return summary

        # Strategy 3: Search in CodeMapping by content_preview
        mapping_stmt = select(CodeMapping).where(
            CodeMapping.content_preview.like(f"%{name}%")
        )
        mapping = self.session.exec(mapping_stmt).first()
        if mapping:
            summary_stmt = select(Summary).where(Summary.id == mapping.summary_id)
            return self.session.exec(summary_stmt).first()

        # Strategy 4: Search in summary text for function/class names
        summary_stmt = (
            select(Summary)
            .where(Summary.text.like(f"%{name}%"))
            .where(Summary.level.in_(["function", "class"]))
        )
        summary = self.session.exec(summary_stmt).first()
        if summary:
            return summary

        return None

    # ========== UTILITY METHODS ==========

    def get_all_summaries_by_level(self, level: str) -> List[Summary]:
        """Get all summaries of a specific level (repository, file, function, etc.)"""
        statement = select(Summary).where(Summary.level == level)
        return list(self.session.exec(statement).all())

    def get_summary_by_id(self, summary_id: str) -> Optional[Summary]:
        """Get a specific summary by ID"""
        statement = select(Summary).where(Summary.id == summary_id)
        return self.session.exec(statement).first()

    def delete_summary(self, summary_id: str) -> bool:
        """Delete a summary and its related data"""
        # Delete code mappings first (foreign key constraint)
        mapping_stmt = select(CodeMapping).where(CodeMapping.summary_id == summary_id)
        mappings = self.session.exec(mapping_stmt).all()
        for mapping in mappings:
            self.session.delete(mapping)

        # Delete dependencies
        dep_stmt = select(Dependency).where(
            or_(Dependency.source_id == summary_id, Dependency.target_id == summary_id)
        )
        dependencies = self.session.exec(dep_stmt).all()
        for dep in dependencies:
            self.session.delete(dep)

        # Delete summary
        summary_stmt = select(Summary).where(Summary.id == summary_id)
        summary = self.session.exec(summary_stmt).first()
        if summary:
            self.session.delete(summary)
            self.session.commit()
            return True
        return False

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the complete dependency graph as a dictionary"""
        statement = select(Dependency)
        dependencies = self.session.exec(statement).all()

        graph = {}
        for dep in dependencies:
            if dep.source_id not in graph:
                graph[dep.source_id] = []
            graph[dep.source_id].append(dep.target_id)

        return graph
