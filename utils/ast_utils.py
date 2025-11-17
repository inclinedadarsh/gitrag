import ast
import os
from typing import Optional, Tuple


def _safe_unparse(node: Optional[ast.AST]) -> Optional[str]:
    """Return Python source for an AST node when possible, else None."""
    if node is None:
        return None
    # ast.unparse is available in Python 3.9+
    unparse = getattr(ast, "unparse", None)
    if callable(unparse):
        try:
            return unparse(node)
        except Exception:
            return None
    return None


def get_docstring(node: ast.AST) -> Optional[str]:
    """
    Extract a cleaned docstring for any AST node that supports it.
    """
    try:
        return ast.get_docstring(node)
    except Exception:
        return None


def _max_lineno_in_subtree(node: ast.AST) -> int:
    """Compute the maximum lineno among a node and all its descendants."""
    max_lineno = getattr(node, "lineno", 0) or 0
    for descendant in ast.walk(node):
        ln = getattr(descendant, "lineno", 0) or 0
        if ln > max_lineno:
            max_lineno = ln
        end_ln = getattr(descendant, "end_lineno", 0) or 0
        if end_ln > max_lineno:
            max_lineno = end_ln
    return max_lineno


def get_source_lines(
    node: ast.AST, filepath: str
) -> Tuple[Optional[int], Optional[int]]:
    """
    Best-effort extraction of start and end line numbers for a node.
    Returns (line_start, line_end) using 1-based line numbers.
    """
    line_start = getattr(node, "lineno", None)
    # Prefer PEP 626 end_lineno when available
    end_lineno = getattr(node, "end_lineno", None)
    if line_start is not None and end_lineno is not None:
        return line_start, end_lineno

    if line_start is None:
        return None, None

    # Fallback: approximate end by scanning subtree for maximum line number
    try:
        approx_end = _max_lineno_in_subtree(node)
        if approx_end and approx_end >= line_start:
            return line_start, approx_end
    except Exception:
        pass

    # Last resort: read file and bound to file length
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            total_lines = sum(1 for _ in f)
        return line_start, total_lines
    except Exception:
        return line_start, None


def resolve_import_to_filepath(import_name: str, repo_path: str) -> Optional[str]:
    """
    Attempt to resolve a Python import (dotted path) to an in-repo file path.
    Returns a path relative to repo_path if resolvable, else None.
    Examples:
      "package.module" -> "package/module.py" if exists
      "package" -> "package/__init__.py" if exists
    """
    # Normalize inputs
    if not import_name:
        return None
    sanitized = import_name.strip()
    if not sanitized:
        return None

    # Remove leading dots from relative imports; we cannot resolve them without context
    while sanitized.startswith("."):
        sanitized = sanitized[1:]

    if not sanitized:
        return None

    parts = sanitized.split(".")
    candidate_module = os.path.join(repo_path, *parts) + ".py"
    candidate_package_init = os.path.join(repo_path, *parts, "__init__.py")

    if os.path.isfile(candidate_module):
        return os.path.relpath(candidate_module, repo_path)
    if os.path.isfile(candidate_package_init):
        return os.path.relpath(candidate_package_init, repo_path)

    return None
