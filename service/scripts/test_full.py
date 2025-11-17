from openai import OpenAI
from sqlmodel import Session, create_engine
from sqlalchemy import text
from core.parser import CodeParser
from core.summarizer import SummaryGenerator
from core.db_manager import DatabaseManager
from app.db import create_db_and_tables

# 1) Setup database
engine = create_engine("sqlite:///database.db")
create_db_and_tables()
session = Session(engine)

# Clear existing data to avoid conflicts
print("Clearing existing data...")

# Delete all existing data using raw SQL
session.exec(text("DELETE FROM summary"))
session.exec(text("DELETE FROM codemapping"))
session.exec(text("DELETE FROM dependency"))
session.commit()

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

# Store ALL file summaries and components
for file_meta in parsed_repo["files"]:  # Process ALL files
    filepath = file_meta["filepath"]
    print("running for file: ", filepath)
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

    # Store code mapping for ALL files (not just those with functions/classes)
    db_manager.insert_code_mapping(
        summary_id=file_id,
        filepath=filepath,
        line_start=1,
        line_end=100,  # Approximate
        element_type="file",
        content_preview=f"File: {filepath}",
    )

    # Store function summaries (ALL functions, not just first 2)
    for idx, func in enumerate(file_meta.get("functions", [])):
        func_id = (
            f"func_{filepath.replace('/', '_').replace('.', '_')}_{func['name']}_{idx}"
        )
        print("running for function: ", func_id)
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

    # Store class summaries (ALL classes)
    for idx, cls in enumerate(file_meta.get("classes", [])):
        cls_id = (
            f"class_{filepath.replace('/', '_').replace('.', '_')}_{cls['name']}_{idx}"
        )
        print("running for class: ", cls_id)
        cls_summary = summarizer.generate_component_summary(cls, "class")

        db_manager.insert_summary(
            summary_id=cls_id,
            level="class",
            text=cls_summary,
            token_count=len(cls_summary.split()),
            parent_id=file_id,
            target_id=cls["name"],
        )

        # Store code mapping for class
        if cls.get("line_start") and cls.get("line_end"):
            db_manager.insert_code_mapping(
                summary_id=cls_id,
                filepath=filepath,
                line_start=cls["line_start"],
                line_end=cls["line_end"],
                element_type="class",
                content_preview=cls["name"],
            )

# Store dependencies from the parsed dependency graph
print("Storing dependencies...")
dependency_graph = parsed_repo.get("dependency_graph", {})
for source_file, target_files in dependency_graph.items():
    source_file_id = f"file_{source_file.replace('/', '_').replace('.', '_')}"

    for target_file in target_files:
        # Check if target is an external dependency (not a file in repo)
        if not target_file.endswith(".py"):
            # External dependency
            target_id = f"external_{target_file}"
            db_manager.insert_dependency(
                source_id=source_file_id, target_id=target_id, relationship="imports"
            )
        else:
            # Internal file dependency
            target_file_id = f"file_{target_file.replace('/', '_').replace('.', '_')}"
            db_manager.insert_dependency(
                source_id=source_file_id,
                target_id=target_file_id,
                relationship="imports",
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

# Get all function summaries
func_summaries = db_manager.get_all_summaries_by_level("function")
print(f"Total function summaries in DB: {len(func_summaries)}")

# Get all class summaries
class_summaries = db_manager.get_all_summaries_by_level("class")
print(f"Total class summaries in DB: {len(class_summaries)}")

# Get dependency graph
graph = db_manager.get_dependency_graph()
print(f"Dependency graph has {len(graph)} relationships")

# Show some specific examples
print(f"\nFiles processed: {[f['filepath'] for f in parsed_repo['files']]}")

print("\nDone! Check database.db for stored data.")
