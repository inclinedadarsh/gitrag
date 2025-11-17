"""
Models for storing summaries and code mappings.
"""

from typing import Optional
from sqlmodel import Field, SQLModel, Column, JSON
from datetime import datetime, timezone


class Summary(SQLModel, table=True):
    """
    Stores hierarchical summaries.

    Attributes:
        id: Unique identifier (composite: level_target)
        level: "repository" | "file" | "function" | "class" | "markdown_section"
        type: "compact" | "full" (only for file-level)
        target_id: Which component this summarizes
        text: The actual summary text
        token_count: Number of tokens in summary
        parent_id: For components, which file/section contains them
        metadata_: JSON field for flexible extra data
    """

    id: str = Field(
        primary_key=True
    )  # e.g., "file_auth_login" or "func_authenticate_user"
    level: str  # repository, file, function, class, markdown_section
    type: Optional[str] = None  # compact, full
    target_id: str  # What this summarizes
    text: str  # The summary text (long text)
    token_count: int  # For tracking usage
    parent_id: Optional[str] = None  # file_id for functions, repo_id for files
    metadata_: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CodeMapping(SQLModel, table=True):
    """
    Maps summaries to actual source code locations.

    Attributes:
        summary_id: Foreign key to Summary
        filepath: Where the code is (auth/login.py)
        line_start: Starting line number
        line_end: Ending line number
        element_type: "function" | "class" | "markdown_section"
        content_preview: First 200 chars of actual code
    """

    summary_id: str = Field(foreign_key="summary.id", primary_key=True)
    filepath: str  # e.g., "auth/login.py"
    line_start: int
    line_end: int
    element_type: str  # function, class, markdown_section
    content_preview: Optional[str] = None  # First 200 chars of code
