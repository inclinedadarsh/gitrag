"""
Pydantic models for API request/response schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for asking questions about the codebase."""

    query: str
    user_id: str = "default"
    conversation_history: Optional[List[Dict[str, Any]]] = None


class QueryResponse(BaseModel):
    """Response model for query answers."""

    answer: str
    sources: List[Dict[str, Any]]
    new_concepts: List[str]
    follow_up_suggestions: List[str]
    confidence: float
    processing_time: float
    tools_used: List[str]


class InitializeRequest(BaseModel):
    """Request model for initializing a repository."""

    repo_path: str
    user_id: Optional[str] = "default"


class InitializeResponse(BaseModel):
    """Response model for repository initialization."""

    status: str
    files_parsed: int
    components_processed: int
    dependencies_stored: int
    repository_name: str
    processing_time: float
    message: str


class UserKnowledgeResponse(BaseModel):
    """Response model for user knowledge."""

    concepts_learned: List[str]
    expertise_level: str
    components_explored: List[str]
    total_queries: int
    last_activity: Optional[str] = None


class ComponentResponse(BaseModel):
    """Response model for component details."""

    summary: str
    code_location: Dict[str, Any]
    related_components: List[Dict[str, Any]]
    usage_examples: List[str]
    dependencies: List[str]
    dependents: List[str]
    file_path: str


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str
    detail: Optional[str] = None
    status_code: int


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str
    database_connected: bool
    pipeline_ready: bool
