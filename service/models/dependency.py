"""
Models for storing dependencies between code components.
"""

from sqlmodel import Field, SQLModel
from datetime import datetime, timezone


class Dependency(SQLModel, table=True):
    """
    Stores relationships between code components.

    Attributes:
        source_id: Which summary calls/imports/uses
        target_id: Which summary is being called/imported
        relationship: Type of relationship
    """

    source_id: str = Field(foreign_key="summary.id", primary_key=True)
    target_id: str = Field(foreign_key="summary.id", primary_key=True)
    relationship: str  # "calls", "imports", "inherits", "contains"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
