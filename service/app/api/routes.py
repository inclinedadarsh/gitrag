"""
FastAPI routes for the application.
"""

import time
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.schemas import (
    QueryRequest,
    QueryResponse,
    InitializeRequest,
    InitializeResponse,
    UserKnowledgeResponse,
    ComponentResponse,
    HealthResponse,
)
from core import CodeUnderstandingPipeline
from core.db_manager import DatabaseManager

router = APIRouter()

# Global pipeline instance (in production, this would be managed differently)
_pipeline: CodeUnderstandingPipeline = None


def get_pipeline() -> CodeUnderstandingPipeline:
    """Get or create the pipeline instance."""
    global _pipeline
    if _pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized. Please call /initialize first.",
        )
    return _pipeline


@router.post("/query", response_model=QueryResponse)
async def ask_query(
    request: QueryRequest, session: Session = Depends(get_session)
) -> QueryResponse:
    """
    Main endpoint: ask a question about the codebase.

    Request:
    {
        "query": "How does authentication work?",
        "user_id": "user123",
        "conversation_history": [...]
    }

    Response:
    {
        "answer": "Authentication in this project...",
        "sources": [...],
        "new_concepts": ["authentication_flow"],
        "follow_up_suggestions": [...]
    }
    """
    start_time = time.time()

    try:
        # Get pipeline
        pipeline = get_pipeline()

        # Process the query
        response = pipeline.answer_user_query(
            query=request.query, user_id=request.user_id
        )

        processing_time = time.time() - start_time

        # Generate follow-up suggestions based on the query and response
        follow_up_suggestions = _generate_follow_up_suggestions(
            request.query, response.get("answer", "")
        )

        return QueryResponse(
            answer=response["answer"],
            sources=_format_sources(response.get("sources", [])),
            new_concepts=response.get("new_concepts_learned", []),
            follow_up_suggestions=follow_up_suggestions,
            confidence=response.get("confidence", 0.0),
            processing_time=processing_time,
            tools_used=response.get("tools_used", []),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/initialize", response_model=InitializeResponse)
async def initialize_repo(
    request: InitializeRequest, session: Session = Depends(get_session)
) -> InitializeResponse:
    """
    Initialize the system with a repository.

    Request:
    {
        "repo_path": "/path/to/repo"
    }

    Response:
    {
        "status": "success",
        "files_parsed": 45,
        "summaries_generated": 120,
        "token_count": 45000
    }
    """
    start_time = time.time()

    try:
        global _pipeline

        # Initialize pipeline
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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",
        )

        _pipeline = CodeUnderstandingPipeline(
            repo_path=request.repo_path, llm_client=client, db_session=session
        )

        # Initialize repository
        result = _pipeline.initialize_repository()

        processing_time = time.time() - start_time

        return InitializeResponse(
            status="success",
            files_parsed=result["files_processed"],
            components_processed=result["components_processed"],
            dependencies_stored=result["dependencies_stored"],
            repository_name=result["repository_name"],
            processing_time=processing_time,
            message=f"Successfully initialized repository with {result['files_processed']} files",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error initializing repository: {str(e)}"
        )


@router.get("/user/{user_id}/knowledge", response_model=UserKnowledgeResponse)
async def get_user_knowledge(
    user_id: str, session: Session = Depends(get_session)
) -> UserKnowledgeResponse:
    """
    Get what a user has learned.

    Response:
    {
        "concepts_learned": ["authentication_flow", "database_queries"],
        "expertise_level": "beginner",
        "components_explored": [...]
    }
    """
    try:
        # For now, return mock data since user knowledge tracking isn't fully implemented
        # In a real implementation, this would query the UserKnowledge table

        return UserKnowledgeResponse(
            concepts_learned=["neural_networks", "loss_functions", "optimization"],
            expertise_level="intermediate",
            components_explored=["Loss", "MSE", "NeuralNet", "train"],
            total_queries=0,
            last_activity=None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving user knowledge: {str(e)}"
        )


@router.get("/component/{component_name}", response_model=ComponentResponse)
async def get_component_details(
    component_name: str, session: Session = Depends(get_session)
) -> ComponentResponse:
    """
    Get detailed information about a specific component.

    Response:
    {
        "summary": "...",
        "code_location": {"file": "auth/login.py", "lines": "15-30"},
        "related_components": [...],
        "usage_examples": [...]
    }
    """
    try:
        db_manager = DatabaseManager(session)

        # Search for the component
        component_summary = db_manager.search_by_component_name(component_name)

        if not component_summary:
            raise HTTPException(
                status_code=404, detail=f"Component '{component_name}' not found"
            )

        # Get related components (dependencies and dependents)
        dependencies = db_manager.get_dependencies_of_component(
            component_summary.id, "calls"
        )
        dependents = db_manager.get_dependents_of_component(
            component_summary.id, "calls"
        )

        # Get code location from CodeMapping
        code_location = _get_code_location(db_manager, component_summary.id)

        # Generate usage examples (simplified)
        usage_examples = _generate_usage_examples(
            component_name, component_summary.text
        )

        return ComponentResponse(
            summary=component_summary.text,
            code_location=code_location,
            related_components=_format_related_components(dependencies + dependents),
            usage_examples=usage_examples,
            dependencies=[dep.target_id for dep in dependencies],
            dependents=[dep.target_id for dep in dependents],
            file_path=code_location.get("file", "Unknown"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving component details: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(session: Session = Depends(get_session)) -> HealthResponse:
    """Health check endpoint."""
    try:
        # Test database connection
        session.exec("SELECT 1").first()
        database_connected = True
    except:  # noqa: E722
        database_connected = False

    return HealthResponse(
        status="healthy" if database_connected else "unhealthy",
        version="1.0.0",
        database_connected=database_connected,
        pipeline_ready=_pipeline is not None,
    )


def _format_sources(sources: list) -> list:
    """Format sources for API response."""
    formatted_sources = []
    for source in sources:
        if hasattr(source, "target_id") and hasattr(source, "text"):
            formatted_sources.append(
                {
                    "id": source.target_id,
                    "type": source.level,
                    "content": source.text[:200] + "..."
                    if len(source.text) > 200
                    else source.text,
                    "relevance": 0.8,  # Could be calculated based on context
                }
            )
    return formatted_sources


def _generate_follow_up_suggestions(query: str, answer: str) -> list:
    """Generate follow-up suggestions based on query and answer."""
    suggestions = []

    # Simple keyword-based suggestions
    if "loss" in query.lower():
        suggestions.extend(
            [
                "How is the loss function used in training?",
                "What are the different types of loss functions available?",
                "How do you calculate gradients for the loss function?",
            ]
        )
    elif "neural" in query.lower() or "network" in query.lower():
        suggestions.extend(
            [
                "How do you create a neural network?",
                "What layers are available in this library?",
                "How do you train a neural network?",
            ]
        )
    elif "train" in query.lower():
        suggestions.extend(
            [
                "What parameters can you pass to the training function?",
                "How do you monitor training progress?",
                "What optimizers are available?",
            ]
        )

    # Generic suggestions
    suggestions.extend(
        [
            "Can you show me an example of how to use this?",
            "What are the dependencies of this component?",
            "Where is this component defined in the code?",
        ]
    )

    return suggestions[:5]  # Return top 5 suggestions


def _get_code_location(
    db_manager: DatabaseManager, component_id: str
) -> Dict[str, Any]:
    """Get code location information for a component."""
    # This would query CodeMapping table for the component
    # For now, return mock data
    return {"file": "inclinet/loss.py", "lines": "15-30", "column": 0}


def _format_related_components(components: list) -> list:
    """Format related components for API response."""
    formatted = []
    for comp in components:
        if hasattr(comp, "target_id") and hasattr(comp, "text"):
            formatted.append(
                {
                    "name": comp.target_id,
                    "type": comp.level,
                    "summary": comp.text[:100] + "..."
                    if len(comp.text) > 100
                    else comp.text,
                }
            )
    return formatted


def _generate_usage_examples(component_name: str, summary: str) -> list:
    """Generate usage examples for a component."""
    examples = []

    if component_name.lower() == "loss":
        examples.extend(
            [
                "loss_fn = Loss()\nresult = loss_fn.loss(predicted, target)",
                "mse = MSE()\nerror = mse.loss(predictions, labels)",
            ]
        )
    elif component_name.lower() == "neuralnet":
        examples.extend(
            [
                "net = NeuralNet([Linear(2, 4), Tanh(), Linear(4, 1)])",
                "output = net.forward(input_data)",
            ]
        )

    return examples
