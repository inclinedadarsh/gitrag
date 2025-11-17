"""
FastAPI application for GitRAG service.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.routes import router
from app.db import create_db_and_tables
from app.schemas import ErrorResponse

# Create FastAPI app
app = FastAPI(
    title="GitRAG Service",
    description="AI-powered code understanding and question answering service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        create_db_and_tables()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🔄 Shutting down GitRAG service...")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.detail, status_code=exc.status_code).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error", detail=str(exc), status_code=500
        ).dict(),
    )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "GitRAG Service",
        "version": "1.0.0",
        "description": "AI-powered code understanding and question answering",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "query": "/api/v1/query",
            "initialize": "/api/v1/initialize",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
