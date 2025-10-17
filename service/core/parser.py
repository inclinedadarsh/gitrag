import os
import ast
import re
import subprocess
from typing import Dict, List, Optional, Any

from utils.ast_utils import (
    get_docstring,
    get_source_lines,
    resolve_import_to_filepath,
)


class CodeParser:
    """
    Extracts structural metadata from Python and Markdown files.

    Attributes:
        repo_path: str - root directory to parse
        supported_extensions: list - ['.py', '.md']
    """

    def __init__(self, github_repo_url: str, base_dir: Optional[str] = None) -> None:
        """Initialize parser with GitHub repo URL; clone if missing."""
        self.github_repo_url = github_repo_url.rstrip("/")
        self.supported_extensions = [".py", ".md"]
        self.repo_path = self.clone_repo(base_dir=base_dir)

    def clone_repo(self, base_dir: Optional[str] = None) -> str:
        """
        Clone the repository into base_dir/repos/<name> if it doesn't exist yet.
        Returns the absolute path to the local repository directory.
        """
        base = base_dir or os.path.join(os.getcwd(), "repos")
        os.makedirs(base, exist_ok=True)

        # Derive repository directory name from URL
        repo_name = self.github_repo_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        repo_path = os.path.join(base, repo_name)
        if not os.path.exists(repo_path):
            subprocess.run(
                ["git", "clone", "--depth=1", self.github_repo_url, repo_path],
                check=True,
            )
        return os.path.abspath(repo_path)

    # ------------------------------- Public API ---------------------------------
    def parse_repository(self) -> Dict[str, Any]:
        """
        Entry point: parses entire repo and returns structured JSON.

        Returns:
            {
                "repository": {...},
                "files": [file1, file2, ...],
                "dependency_graph": {...}
            }
        """
        files_metadata: List[Dict[str, Any]] = []

        for root, _dirs, files in os.walk(self.repo_path):
            for filename in files:
                _, ext = os.path.splitext(filename)
                if ext not in self.supported_extensions:
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, self.repo_path)
                try:
                    if ext == ".py":
                        files_metadata.append(self.parse_python_file(rel_path))
                    elif ext == ".md":
                        files_metadata.append(self.parse_markdown_file(rel_path))
                except Exception:
                    # Skip problematic files but continue parsing others
                    continue

        repo_info = {
            "name": os.path.basename(self.repo_path.rstrip(os.sep)),
            "path": self.repo_path,
            "type": "python",
            "files_count": len(files_metadata),
        }

        dependency_graph = self._build_dependency_graph(files_metadata)

        return {
            "repository": repo_info,
            "files": files_metadata,
            "dependency_graph": dependency_graph,
        }

    # ---------------------------- Python parsing --------------------------------
    def parse_python_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a single Python file using AST.
        """
        full_path = os.path.join(self.repo_path, filepath)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        module = ast.parse(source)

        imports: List[str] = []
        functions: List[Dict[str, Any]] = []
        classes: List[Dict[str, Any]] = []

        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name:
                        imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                # Handle relative imports conservatively; keep module if available
                module_name = node.module or ""
                if module_name:
                    imports.append(module_name)
                else:
                    # from . import x -> record names without module context
                    for alias in node.names:
                        if alias.name:
                            imports.append(alias.name)
            elif isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node, full_path)
                functions.append(func_info)
            elif isinstance(node, ast.AsyncFunctionDef):
                func_info = self._extract_function_info(node, full_path)
                functions.append(func_info)
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, full_path)
                classes.append(class_info)

        return {
            "filepath": filepath.replace(os.sep, "/"),
            "type": "python",
            "imports": sorted(list(dict.fromkeys(imports))),
            "functions": functions,
            "classes": classes,
        }

    def _extract_function_info(self, node: ast.AST, full_path: str) -> Dict[str, Any]:
        name = getattr(node, "name", "")
        line_start, line_end = get_source_lines(node, full_path)
        doc = get_docstring(node) or ""
        calls = self._extract_calls_from_function(node) or []
        signature = self._signature_from_functiondef(node)
        complexity = self._cyclomatic_complexity(node)
        return {
            "name": name,
            "signature": signature,
            "line_start": line_start,
            "line_end": line_end,
            "docstring": doc,
            "calls": calls,
            "called_by": [],
            "complexity": complexity,
        }

    def _extract_class_info(self, node: ast.ClassDef, full_path: str) -> Dict[str, Any]:
        line_start, line_end = get_source_lines(node, full_path)
        methods: List[str] = []
        attributes: List[str] = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(child.name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        return {
            "name": node.name,
            "line_start": line_start,
            "line_end": line_end,
            "methods": methods,
            "attributes": attributes,
            "docstring": get_docstring(node) or "",
        }

    # --------------------------- Markdown parsing -------------------------------
    def parse_markdown_file(self, filepath: str) -> Dict[str, Any]:
        full_path = os.path.join(self.repo_path, filepath)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        lines = text.splitlines()

        sections: List[Dict[str, Any]] = []
        current_section: Optional[Dict[str, Any]] = None
        content_lines: List[str] = []

        code_blocks: List[Dict[str, Any]] = []
        in_code = False
        code_lang = ""
        code_buffer: List[str] = []
        code_start_line: Optional[int] = None

        heading_re = re.compile(r"^(#{1,6})\s+(.*)$")

        for idx, line in enumerate(lines, start=1):
            # Code fence start/end
            if line.strip().startswith("```"):
                fence = line.strip()
                if not in_code:
                    in_code = True
                    code_lang = fence[3:].strip()
                    code_buffer = []
                    code_start_line = idx + 1
                else:
                    # end of code block
                    in_code = False
                    block = {
                        "language": code_lang or None,
                        "code": "\n".join(code_buffer),
                        "line_start": code_start_line,
                    }
                    code_blocks.append(block)
                    code_lang = ""
                    code_buffer = []
                    code_start_line = None
                continue

            if in_code:
                code_buffer.append(line)
                continue

            m = heading_re.match(line)
            if m:
                # flush previous section
                if current_section is not None:
                    current_section["content"] = "\n".join(content_lines).strip()
                    current_section["code_blocks"] = [b for b in code_blocks]
                    sections.append(current_section)
                    content_lines = []
                    code_blocks = []
                level = len(m.group(1))
                heading_text = m.group(2).strip()
                current_section = {
                    "heading": heading_text,
                    "level": level,
                    "content": "",
                    "code_blocks": [],
                }
            else:
                content_lines.append(line)

        # flush last section
        if current_section is not None:
            current_section["content"] = "\n".join(content_lines).strip()
            current_section["code_blocks"] = [b for b in code_blocks]
            sections.append(current_section)

        title = None
        for s in sections:
            if s.get("level") == 1:
                title = s.get("heading")
                break
        if not title:
            title = os.path.splitext(os.path.basename(full_path))[0]

        return {
            "filepath": filepath.replace(os.sep, "/"),
            "type": "markdown",
            "title": title,
            "sections": sections,
        }

    # ------------------------------- Helpers ------------------------------------
    def _extract_calls_from_function(self, func_node: ast.AST) -> List[str]:
        calls: List[str] = []

        def dotted_name(expr: ast.AST) -> Optional[str]:
            if isinstance(expr, ast.Name):
                return expr.id
            if isinstance(expr, ast.Attribute):
                parts: List[str] = []
                cur: Optional[ast.AST] = expr
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                    return ".".join(reversed(parts))
            return None

        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                name = dotted_name(node.func)
                if name:
                    calls.append(name)
        # keep stable order while removing duplicates
        seen = set()
        unique_calls: List[str] = []
        for c in calls:
            if c not in seen:
                unique_calls.append(c)
                seen.add(c)
        return unique_calls

    def _signature_from_functiondef(self, node: ast.AST) -> str:
        name = getattr(node, "name", "function")

        def unparse(expr: Optional[ast.AST]) -> Optional[str]:
            fn = getattr(ast, "unparse", None)
            if callable(fn) and expr is not None:
                try:
                    return fn(expr)
                except Exception:
                    return None
            return None

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return name + "()"

        args = []
        for arg in node.args.posonlyargs:
            ann = unparse(arg.annotation) or ""
            args.append(f"{arg.arg}: {ann}" if ann else arg.arg)
        if node.args.posonlyargs:
            if node.args.args:
                args.append("/")
            else:
                args.append("/")
        for arg in node.args.args:
            ann = unparse(arg.annotation) or ""
            args.append(f"{arg.arg}: {ann}" if ann else arg.arg)
        if node.args.vararg:
            ann = unparse(node.args.vararg.annotation) or ""
            args.append(
                "*"
                + (f"{node.args.vararg.arg}: {ann}" if ann else node.args.vararg.arg)
            )
        elif node.args.kwonlyargs:
            args.append("*")
        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            ann = unparse(arg.annotation) or ""
            part = f"{arg.arg}: {ann}" if ann else arg.arg
            if default is not None:
                d = unparse(default) or "..."
                part += f"={d}"
            args.append(part)
        if node.args.kwarg:
            ann = unparse(node.args.kwarg.annotation) or ""
            args.append(
                "**" + (f"{node.args.kwarg.arg}: {ann}" if ann else node.args.kwarg.arg)
            )

        # handle defaults for positional args (align from the right)
        total_no_defaults = len(node.args.args) - len(node.args.defaults)
        if node.args.defaults:
            for i, default in enumerate(node.args.defaults, start=total_no_defaults):
                try:
                    d = unparse(default) or "..."
                    args[i] = f"{args[i]}={d}"
                except Exception:
                    pass

        ret_ann = unparse(node.returns)
        ret = f" -> {ret_ann}" if ret_ann else ""
        return f"{name}({', '.join(args)}){ret}"

    def _cyclomatic_complexity(self, node: ast.AST) -> str:
        decision_nodes = 0
        for n in ast.walk(node):
            if isinstance(
                n,
                (
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.Try,
                    ast.With,
                    ast.BoolOp,
                    ast.IfExp,
                    ast.comprehension,
                ),
            ):
                decision_nodes += 1
        value = decision_nodes + 1
        if value <= 5:
            return "low"
        if value <= 10:
            return "medium"
        return "high"

    # --------------------------- Dependency graph -------------------------------
    def _build_dependency_graph(
        self, files_metadata: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        graph: Dict[str, List[str]] = {}
        # index imports per file
        file_to_imports: Dict[str, List[str]] = {}
        python_files = [f for f in files_metadata if f.get("type") == "python"]

        for f in python_files:
            relpath = f["filepath"]
            file_to_imports[relpath] = f.get("imports", [])

        for f in python_files:
            relpath = f["filepath"]
            deps: List[str] = []

            # 1) Imports
            for imp in f.get("imports", []):
                resolved = resolve_import_to_filepath(imp, self.repo_path)
                if resolved:
                    deps.append(resolved.replace(os.sep, "/"))
                else:
                    # keep top-level external name
                    deps.append(imp.split(".")[0])

            # 2) Calls - try resolving calls whose first segment matches an import
            imported_toplevels = {i.split(".")[0] for i in f.get("imports", [])}
            for func in f.get("functions", []):
                for call in func.get("calls", []):
                    first = call.split(".")[0]
                    if first in imported_toplevels:
                        resolved = resolve_import_to_filepath(first, self.repo_path)
                        if resolved:
                            dep_path = resolved.replace(os.sep, "/")
                            if dep_path not in deps:
                                deps.append(dep_path)

            # deduplicate, keep order
            seen = set()
            ordered: List[str] = []
            for d in deps:
                if d not in seen:
                    ordered.append(d)
                    seen.add(d)
            graph[relpath] = ordered

        return graph
