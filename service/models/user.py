"""
Models for tracking user knowledge and interactions.
"""

from sqlmodel import Field, SQLModel, Column, JSON
from datetime import datetime
from datetime import timezone


class UserKnowledge(SQLModel, table=True):
    """
    Tracks what the user has learned about the codebase.

    Attributes:
        user_id: Which user
        concept: What they learned (e.g., "authentication_flow")
        components_learned: List of summary_ids they've learned
        expertise_level: "beginner" | "intermediate" | "advanced"
        queries_asked: How many queries have they made?
    """

    id: int = Field(primary_key=True)
    user_id: str
    concept: str  # "authentication_flow", "database_queries", etc.
    summary_ids_learned: list = Field(default=[], sa_column=Column(JSON))
    confidence: float = 0.5  # How well they understand (0.0-1.0)
    expertise_level: str = "beginner"  # auto-calculated from learned concepts
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        table = True
