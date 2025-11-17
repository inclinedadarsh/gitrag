from openai import OpenAI
from sqlmodel import Session, create_engine
from core.parser import CodeParser
from core.summarizer import SummaryGenerator
from core.db_manager import DatabaseManager
from app.db import create_db_and_tables

# 1) Setup database
engine = create_engine("sqlite:///database.db")
create_db_and_tables()
session = Session(engine)

# 2) Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# 3) Parse a GitHub repository
print("Parsing repository...")
parser = CodeParser("https://github.com/inclinedadarsh/inclinet")
parsed_repo = parser.parse_repository()
print(f"Parsed {len(parsed_repo['files'])} files")

# 4) Generate summaries
print("Generating summaries...")
summarizer = SummaryGenerator(client)

# Repository-level summary
repo_summary = summarizer.generate_repository_summary(parsed_repo)
print("Repository summary:", repo_summary[:100] + "...")

# 5) Store in database
print("Storing in database...")
db_manager = DatabaseManager(session)

# Store repository summary
repo_summary_id = "repo_inclinet"
db_manager.insert_summary(
    summary_id=repo_summary_id,
    level="repository",
    text=repo_summary,
    token_count=len(repo_summary.split()),
    target_id="inclinet",
)

# Store file summaries and components
for file_meta in parsed_repo["files"][:3]:  # Process first 3 files
    filepath = file_meta["filepath"]
    file_id = f"file_{filepath.replace('/', '_').replace('.', '_')}"

    # Generate file summary
    file_summary = summarizer.generate_file_summary_compact(file_meta)

    # Store file summary
    db_manager.insert_summary(
        summary_id=file_id,
        level="file",
        text=file_summary,
        token_count=len(file_summary.split()),
        parent_id=repo_summary_id,
        target_id=filepath,
    )

    # Store code mapping
    if file_meta.get("functions") or file_meta.get("classes"):
        db_manager.insert_code_mapping(
            summary_id=file_id,
            filepath=filepath,
            line_start=1,
            line_end=100,  # Approximate
            element_type="file",
            content_preview=f"File: {filepath}",
        )

    # Store function summaries
    for func in file_meta.get("functions", [])[:2]:  # First 2 functions
        func_id = f"func_{func['name']}"
        func_summary = summarizer.generate_component_summary(func, "function")

        db_manager.insert_summary(
            summary_id=func_id,
            level="function",
            text=func_summary,
            token_count=len(func_summary.split()),
            parent_id=file_id,
            target_id=func["name"],
        )

        # Store code mapping for function
        if func.get("line_start") and func.get("line_end"):
            db_manager.insert_code_mapping(
                summary_id=func_id,
                filepath=filepath,
                line_start=func["line_start"],
                line_end=func["line_end"],
                element_type="function",
                content_preview=func.get("signature", func["name"]),
            )

# 6) Query the database
print("\n=== Database Queries ===")

# Get repository summary
repo_from_db = db_manager.get_repository_summary()
print(f"Repository summary from DB: {repo_from_db.text[:100]}...")

# Search by keyword
auth_results = db_manager.search_summaries_by_keyword("network", limit=3)
print(f"Found {len(auth_results)} summaries mentioning 'network'")

# Get all file summaries
file_summaries = db_manager.get_all_summaries_by_level("file")
print(f"Total file summaries in DB: {len(file_summaries)}")

# Get dependency graph
graph = db_manager.get_dependency_graph()
print(f"Dependency graph has {len(graph)} relationships")

print("\nDone! Check database.db for stored data.")
