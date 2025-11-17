"""
Helper functions to build JSON structures and IDs used throughout the system.
"""

import re
from typing import Dict, Any, Optional


def build_summary_id(
    level: str, target_name: str, summary_type: Optional[str] = None
) -> str:
    """
    Create a unique summary ID.

    Examples:
        build_summary_id("repository", "my-project")
        → "repo_my-project"

        build_summary_id("file", "auth/login.py")
        → "file_auth_login_py"

        build_summary_id("function", "authenticate_user")
        → "func_authenticate_user"

        build_summary_id("file", "auth/login.py", "compact")
        → "file_auth_login_py_compact"
    """
    # Normalize target_name by replacing special characters with underscores
    normalized_name = re.sub(r"[^\w\-]", "_", target_name)
    normalized_name = re.sub(
        r"_+", "_", normalized_name
    )  # Collapse multiple underscores
    normalized_name = normalized_name.strip("_")  # Remove leading/trailing underscores

    # Build base ID based on level
    if level == "repository":
        base_id = f"repo_{normalized_name}"
    elif level == "file":
        # Remove file extension and normalize path
        name_without_ext = (
            normalized_name.rsplit(".", 1)[0]
            if "." in normalized_name
            else normalized_name
        )
        base_id = f"file_{name_without_ext}"
    elif level == "function":
        base_id = f"func_{normalized_name}"
    elif level == "class":
        base_id = f"class_{normalized_name}"
    elif level == "markdown_section":
        base_id = f"section_{normalized_name}"
    else:
        base_id = f"{level}_{normalized_name}"

    # Add summary type if provided
    if summary_type:
        base_id = f"{base_id}_{summary_type}"

    return base_id


def build_component_metadata(
    name: str,
    element_type: str,
    signature: str,
    docstring: str,
    line_start: int,
    line_end: int,
) -> Dict[str, Any]:
    """
    Build metadata dict for a component.

    Returns:
    {
        "name": "authenticate_user",
        "type": "function",
        "signature": "authenticate_user(username: str, password: str) -> bool",
        "docstring": "Validates user credentials",
        "line_start": 15,
        "line_end": 30
    }
    """
    return {
        "name": name,
        "type": element_type,
        "signature": signature,
        "docstring": docstring,
        "line_start": line_start,
        "line_end": line_end,
    }


def extract_file_summary_id(filepath: str) -> str:
    """
    Convert filepath to file summary ID.

    "auth/login.py" → "file_auth_login"
    "docs/README.md" → "file_docs_README"
    """
    # Remove leading slash if present
    clean_path = filepath.lstrip("/")

    # Replace path separators and dots with underscores
    normalized = re.sub(r"[/\\]", "_", clean_path)
    normalized = re.sub(r"\.", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)  # Collapse multiple underscores
    normalized = normalized.strip("_")  # Remove leading/trailing underscores

    return f"file_{normalized}"


def extract_component_id_from_mapping(
    component_name: str,
    element_type: str,
    filepath: Optional[str] = None,
    line_start: Optional[int] = None,
) -> str:
    """
    Create component ID from name and type, optionally including filepath for uniqueness.

    "authenticate_user" + "function" → "func_authenticate_user"
    "authenticate_user" + "function" + "auth/login.py" → "func_authenticate_user_auth_login_py"
    "loss" + "function" + "inclinet/loss.py" + 10 → "func_loss_inclinet_loss_py_10"
    "AuthManager" + "class" → "class_AuthManager"
    """
    # Normalize component name
    normalized_name = re.sub(r"[^\w\-]", "_", component_name)
    normalized_name = re.sub(r"_+", "_", normalized_name)
    normalized_name = normalized_name.strip("_")

    # Map element type to prefix
    type_prefix_map = {
        "function": "func",
        "class": "class",
        "method": "method",
        "property": "prop",
        "variable": "var",
        "constant": "const",
        "markdown_section": "section",
    }

    prefix = type_prefix_map.get(element_type, element_type)
    base_id = f"{prefix}_{normalized_name}"

    # Add filepath to make ID unique if provided (handles duplicate names in same file)
    if filepath:
        # Normalize filepath similar to extract_file_summary_id
        clean_path = filepath.lstrip("/")
        normalized_path = re.sub(r"[/\\]", "_", clean_path)
        normalized_path = re.sub(r"\.", "_", normalized_path)
        normalized_path = re.sub(r"_+", "_", normalized_path)
        normalized_path = normalized_path.strip("_")
        base_id = f"{base_id}_{normalized_path}"

    # Add line number if provided (for extra uniqueness if same name in same file)
    if line_start is not None:
        base_id = f"{base_id}_{line_start}"

    return base_id


def build_dependency_relationship(
    source_id: str, target_id: str, relationship_type: str
) -> Dict[str, str]:
    """
    Build a dependency relationship dictionary.

    Args:
        source_id: ID of the component that depends on target
        target_id: ID of the component being depended upon
        relationship_type: "calls", "imports", "inherits", "contains"

    Returns:
    {
        "source_id": "func_authenticate_user",
        "target_id": "func_check_password",
        "relationship": "calls"
    }
    """
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relationship": relationship_type,
    }


def build_code_mapping_data(
    summary_id: str,
    filepath: str,
    line_start: int,
    line_end: int,
    element_type: str,
    content_preview: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build code mapping data structure.

    Args:
        summary_id: ID of the summary this mapping refers to
        filepath: Path to the source file
        line_start: Starting line number
        line_end: Ending line number
        element_type: Type of code element
        content_preview: Optional preview of the code

    Returns:
    {
        "summary_id": "func_authenticate_user",
        "filepath": "auth/login.py",
        "line_start": 15,
        "line_end": 30,
        "element_type": "function",
        "content_preview": "def authenticate_user(username: str, password: str) -> bool:"
    }
    """
    return {
        "summary_id": summary_id,
        "filepath": filepath,
        "line_start": line_start,
        "line_end": line_end,
        "element_type": element_type,
        "content_preview": content_preview,
    }


def build_summary_data(
    summary_id: str,
    level: str,
    text: str,
    token_count: int,
    parent_id: Optional[str] = None,
    summary_type: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build summary data structure for database insertion.

    Args:
        summary_id: Unique identifier for the summary
        level: Summary level (repository, file, function, class, etc.)
        text: The actual summary text
        token_count: Number of tokens in the summary
        parent_id: Parent component ID for hierarchical relationships
        summary_type: Type of summary (compact, full, etc.)
        target_id: What this summary describes
        metadata: Additional metadata as dictionary

    Returns:
    {
        "id": "func_authenticate_user",
        "level": "function",
        "type": "compact",
        "target_id": "authenticate_user",
        "text": "Validates user credentials...",
        "token_count": 15,
        "parent_id": "file_auth_login_py",
        "metadata_": {"complexity": "medium"}
    }
    """
    return {
        "id": summary_id,
        "level": level,
        "type": summary_type,
        "target_id": target_id or summary_id,
        "text": text,
        "token_count": token_count,
        "parent_id": parent_id,
        "metadata_": metadata,
    }


def normalize_filepath(filepath: str) -> str:
    """
    Normalize filepath for consistent storage and retrieval.

    Args:
        filepath: Raw filepath from parser

    Returns:
        Normalized filepath with forward slashes and no leading slash
    """
    # Convert backslashes to forward slashes
    normalized = filepath.replace("\\", "/")

    # Remove leading slash
    normalized = normalized.lstrip("/")

    # Remove trailing slash
    normalized = normalized.rstrip("/")

    return normalized


def extract_module_name_from_filepath(filepath: str) -> str:
    """
    Extract module name from filepath for import resolution.

    "inclinet/neural_network.py" → "inclinet.neural_network"
    "examples/fizzbuzz.py" → "examples.fizzbuzz"
    """
    # Normalize the filepath
    normalized = normalize_filepath(filepath)

    # Remove .py extension
    if normalized.endswith(".py"):
        normalized = normalized[:-3]

    # Convert path separators to dots
    module_name = normalized.replace("/", ".")

    return module_name


def build_hierarchical_summary_structure(
    repo_data: Dict[str, Any], summaries: Dict[str, str]
) -> Dict[str, Any]:
    """
    Build a hierarchical summary structure for API responses.

    Args:
        repo_data: Parsed repository data from CodeParser
        summaries: Dictionary mapping summary IDs to summary text

    Returns:
    {
        "repository": {
            "name": "inclinet",
            "summary": "A neural network library...",
            "files": [
                {
                    "filepath": "inclinet/neural_network.py",
                    "summary": "Core neural network implementation...",
                    "functions": [
                        {
                            "name": "forward",
                            "summary": "Performs forward propagation...",
                            "line_start": 15,
                            "line_end": 30
                        }
                    ]
                }
            ]
        }
    }
    """
    result = {
        "repository": {
            "name": repo_data.get("repository", {}).get("name", "unknown"),
            "summary": summaries.get(
                "repo_" + repo_data.get("repository", {}).get("name", "unknown"), ""
            ),
            "files": [],
        }
    }

    for file_meta in repo_data.get("files", []):
        filepath = file_meta["filepath"]
        file_id = extract_file_summary_id(filepath)

        file_structure = {
            "filepath": filepath,
            "summary": summaries.get(file_id, ""),
            "functions": [],
            "classes": [],
        }

        # Add functions
        for func in file_meta.get("functions", []):
            func_id = extract_component_id_from_mapping(
                func["name"], "function", filepath, func.get("line_start")
            )
            file_structure["functions"].append(
                {
                    "name": func["name"],
                    "summary": summaries.get(func_id, ""),
                    "line_start": func.get("line_start"),
                    "line_end": func.get("line_end"),
                    "signature": func.get("signature", ""),
                }
            )

        # Add classes
        for cls in file_meta.get("classes", []):
            cls_id = extract_component_id_from_mapping(
                cls["name"], "class", filepath, cls.get("line_start")
            )
            file_structure["classes"].append(
                {
                    "name": cls["name"],
                    "summary": summaries.get(cls_id, ""),
                    "line_start": cls.get("line_start"),
                    "line_end": cls.get("line_end"),
                    "methods": cls.get("methods", []),
                }
            )

        result["repository"]["files"].append(file_structure)

    return result
