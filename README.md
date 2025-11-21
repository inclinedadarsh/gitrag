# GitRAG - AI-Powered Code Understanding

GitRAG is an AI-powered code understanding and question answering system. It analyzes code repositories, generates intelligent summaries, and answers questions about codebases using advanced language models.

## Features

- [SEARCH] **Repository Analysis**: Automatically parses and analyzes Python and Markdown files
- [DOCS] **Intelligent Summarization**: Generates hierarchical summaries at repository, file, and component levels
- [LLM] **AI-Powered Q&A**: Ask questions about the codebase and get detailed answers
- [LINK] **Dependency Tracking**: Understand relationships between components
- [MIND] **Context-Aware**: Uses reasoning agents to navigate code context

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/inclinedadarsh/gitrag.git
cd gitrag
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up environment variables:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
export DATABASE_URL="sqlite:///./database.db"  # Optional, defaults to this
export MODE="production" # Optional, defaults to "production" or "dev" for detailed logging
```

## Usage

### Running the Terminal Application

Start the interactive terminal application:

```bash
python main.py
```

Or using uv:

```bash
uv run main.py
```

### Interactive Commands

Once the application starts:

1. **Initialize Repository**: Enter a GitHub repository URL when prompted
   - Example: `https://github.com/username/repository`
   - The system will clone and analyze the repository

2. **Ask Questions**: After initialization, ask questions about the codebase
   - Example: "What does this project do?"
   - Example: "How does the authentication function work?"
   - Example: "Where is the main entry point?"

3. **Available Commands**:
   - `/help` - Show help message
   - `/reset` - Reset and initialize a new repository
   - `/exit` or `/quit` - Exit the application

## Testing

The project includes comprehensive test scripts for each component:

### Individual Component Tests

```bash
# Test the parser
python scripts/test_parser.py

# Test the summarizer
python scripts/test_summarizer.py

# Test the classifier
python scripts/test_classifier.py

# Test the retrieval engine
python scripts/test_retrieval.py

# Test the agent
python scripts/test_agent.py

# Test the database manager
python scripts/test_db_manager.py
```

### Full Pipeline Test

```bash
# Test the complete pipeline (initialization + queries)
python scripts/test_pipeline.py
```

## Architecture

### Core Components

- **CodeParser** (`core/parser.py`): Parses Python and Markdown files, extracts structure
- **SummaryGenerator** (`core/summarizer.py`): Generates AI-powered summaries
- **QueryClassifier** (`core/classifier.py`): Classifies user queries to determine retrieval strategy
- **RetrievalEngine** (`core/retrieval.py`): Retrieves relevant context from the database
- **LLMAgent** (`core/agent.py`): Reasoning agent that navigates code context
- **DatabaseManager** (`core/db_manager.py`): Manages database operations
- **CodeUnderstandingPipeline** (`core/__init__.py`): Main orchestrator

### Database Models

- **Summary**: Stores summaries at different levels (repository, file, function, class)
- **CodeMapping**: Maps summaries to source code locations
- **Dependency**: Tracks relationships between components
- **UserKnowledge**: Tracks user learning progress (future feature)

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: API key for OpenRouter (defaults to a test key if not set)
- `DATABASE_URL`: Database connection string (defaults to `sqlite:///./database.db`)

### Model Configuration

The system uses `x-ai/grok-code-fast-1` by default. This can be changed in `utils/constants.py`.

## Project Structure

```
gitrag/
|-- main.py                 # Terminal application entry point
|-- core/                   # Core functionality modules
|   |-- agent.py            # LLM reasoning agent
|   |-- classifier.py       # Query classification
|   |-- db_manager.py       # Database operations
|   |-- parser.py           # Code parsing
|   |-- retrieval.py        # Context retrieval
|   |-- summarizer.py       # Summary generation
|   `-- __init__.py         # Pipeline orchestrator
|-- models/                 # Database models
|   |-- summary.py
|   |-- dependency.py
|   `-- user.py
|-- app/                    # Application utilities
|   `-- db.py               # Database setup
|-- utils/                  # Utility functions
|   |-- constants.py        # Constants and prompts
|   |-- json_builder.py     # ID generation utilities
|   `-- ast_utils.py        # AST utilities
`-- scripts/                # Test scripts
    |-- test_parser.py
    |-- test_summarizer.py
    |-- test_classifier.py
    |-- test_retrieval.py
    |-- test_agent.py
    |-- test_db_manager.py
    `-- test_pipeline.py
```

## How It Works

1. **Initialization**: 
   - Clones the repository (if needed)
   - Parses all Python and Markdown files
   - Generates summaries at multiple levels
   - Stores everything in the database

2. **Query Processing**:
   - Classifies the query to determine retrieval strategy
   - Retrieves relevant context from the database
   - Uses reasoning agent to navigate and gather more context
   - Generates a comprehensive answer

3. **Context Navigation**:
   - Agent uses tools to explore code relationships
   - Traces execution paths
   - Finds related components
   - Retrieves full file contents when needed

## Limitations

- Currently supports Python and Markdown files only
- Requires OpenRouter API access (or compatible OpenAI API)
- Initialization can take time for large repositories
- Database grows with repository size

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with OpenAI-compatible APIs via OpenRouter
- Uses SQLModel for database management
- AST parsing for Python code analysis

