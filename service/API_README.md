# GitRAG FastAPI Service

AI-powered code understanding and question answering service built with FastAPI.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python start_server.py
```

### 3. Access the API
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Base URL**: http://localhost:8000/api/v1

## 📚 API Endpoints

### 1. Initialize Repository
**POST** `/api/v1/initialize`

Initialize the system with a repository for analysis.

```json
{
  "repo_path": "https://github.com/username/repository",
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "status": "success",
  "files_parsed": 45,
  "components_processed": 120,
  "dependencies_stored": 89,
  "repository_name": "repository",
  "processing_time": 12.5,
  "message": "Successfully initialized repository with 45 files"
}
```

### 2. Ask Questions
**POST** `/api/v1/query`

Ask questions about the codebase.

```json
{
  "query": "How does authentication work?",
  "user_id": "user123",
  "conversation_history": []
}
```

**Response:**
```json
{
  "answer": "Authentication in this project uses JWT tokens...",
  "sources": [
    {
      "id": "auth_login",
      "type": "function",
      "content": "The login function handles user authentication...",
      "relevance": 0.9
    }
  ],
  "new_concepts": ["jwt_authentication", "session_management"],
  "follow_up_suggestions": [
    "How do you validate JWT tokens?",
    "What are the security considerations?"
  ],
  "confidence": 0.85,
  "processing_time": 2.3,
  "tools_used": ["find_component_file", "get_full_file"]
}
```

### 3. Get Component Details
**GET** `/api/v1/component/{component_name}`

Get detailed information about a specific component.

**Response:**
```json
{
  "summary": "The Loss class computes loss values for neural networks...",
  "code_location": {
    "file": "inclinet/loss.py",
    "lines": "15-30",
    "column": 0
  },
  "related_components": [
    {
      "name": "MSE",
      "type": "class",
      "summary": "Mean Squared Error loss implementation..."
    }
  ],
  "usage_examples": [
    "loss_fn = Loss()\nresult = loss_fn.loss(predicted, target)"
  ],
  "dependencies": ["numpy"],
  "dependents": ["train", "backward"],
  "file_path": "inclinet/loss.py"
}
```

### 4. Get User Knowledge
**GET** `/api/v1/user/{user_id}/knowledge`

Get what a user has learned from previous queries.

**Response:**
```json
{
  "concepts_learned": ["neural_networks", "loss_functions"],
  "expertise_level": "intermediate",
  "components_explored": ["Loss", "NeuralNet", "train"],
  "total_queries": 15,
  "last_activity": "2024-01-15T10:30:00Z"
}
```

### 5. Health Check
**GET** `/api/v1/health`

Check service health and status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database_connected": true,
  "pipeline_ready": true
}
```

## 🧪 Testing

Run the test suite:
```bash
python test_api.py
```

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: Database connection string (default: `sqlite:///./database.db`)

### API Configuration
- **Host**: `0.0.0.0`
- **Port**: `8000`
- **Reload**: `True` (development mode)

## 📖 Example Usage

### Using curl
```bash
# Initialize repository
curl -X POST "http://localhost:8000/api/v1/initialize" \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "https://github.com/username/repo"}'

# Ask a question
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How does the loss function work?", "user_id": "user1"}'
```

### Using Python requests
```python
import requests

# Initialize
response = requests.post("http://localhost:8000/api/v1/initialize", 
  json={"repo_path": "https://github.com/username/repo"})

# Query
response = requests.post("http://localhost:8000/api/v1/query",
  json={"query": "What does this project do?", "user_id": "user1"})
print(response.json()["answer"])
```

## 🏗️ Architecture

The service consists of:

1. **FastAPI Application** (`app/main.py`) - Main web server
2. **API Routes** (`app/api/routes.py`) - Endpoint implementations
3. **Database Layer** (`app/db.py`) - Database configuration
4. **Pydantic Models** (`app/schemas.py`) - Request/response schemas
5. **Core Pipeline** (`core/`) - AI processing pipeline
6. **Database Models** (`models.py`) - SQLModel definitions

## 🚨 Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `404` - Not found
- `500` - Internal server error
- `503` - Service unavailable (pipeline not initialized)

Error responses include:
```json
{
  "error": "Error message",
  "detail": "Additional details",
  "status_code": 500
}
```
