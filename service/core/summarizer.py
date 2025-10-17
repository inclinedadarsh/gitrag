from typing import Any, Dict, List, Optional

from utils.constants import (
    OPENROUTER_MODEL,
    SYSTEM_SUMMARY_MESSAGE,
    REPO_SUMMARY_PROMPT,
    COMPONENT_SUMMARY_PROMPT,
    FILE_COMPACT_SUMMARY_PROMPT,
    FILE_FULL_SUMMARY_PROMPT,
)


class SummaryGenerator:
    """
    Generates hierarchical summaries using LLM.

    Attributes:
        llm_client: OpenAI-compatible client (OpenRouter)
        token_counter: optional callable to track token usage
    """

    def __init__(self, llm_client, token_counter: Optional[callable] = None) -> None:
        """Initialize with LLM client"""
        self.llm = llm_client
        self.token_counter = token_counter
        self.model = OPENROUTER_MODEL

    # ----------------------------- LLM helpers ----------------------------------
    def _chat(self, user_prompt: str, system_prompt: Optional[str] = None) -> str:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = self.llm.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=350,
        )
        text = response.choices[0].message.content.strip()
        if self.token_counter is not None:
            usage = getattr(response, "usage", None)
            if usage is not None:
                self.token_counter(usage)
        return text

    # ------------------------ Repository summary --------------------------------
    def generate_repository_summary(self, parsed_repo: Dict[str, Any]) -> str:
        # Collect modules/dirs, key classes/functions, dependencies
        files = parsed_repo.get("files", [])
        modules = sorted(
            {f.get("filepath", "").split("/")[0] for f in files if f.get("filepath")}
        )
        classes = []
        functions = []
        dependencies = set()
        for f in files:
            if f.get("type") == "python":
                for c in f.get("classes", []):
                    name = c.get("name")
                    if name:
                        classes.append(name)
                for fn in f.get("functions", []):
                    name = fn.get("name")
                    if name:
                        functions.append(name)
                for imp in f.get("imports", []):
                    dependencies.add(imp.split(".")[0])

        prompt = REPO_SUMMARY_PROMPT.format(
            repo_name=parsed_repo.get("repository", {}).get("name") or "(unknown)",
            modules=", ".join(modules) or "(none)",
            classes=", ".join(sorted(set(classes))[:30]) or "(none)",
            functions=", ".join(sorted(set(functions))[:30]) or "(none)",
            dependencies=", ".join(sorted(dependencies)[:30]) or "(none)",
        )
        return self._chat(prompt, system_prompt=SYSTEM_SUMMARY_MESSAGE)

    # -------------------------- File summaries ----------------------------------
    def generate_file_summary_compact(self, file_metadata: Dict[str, Any]) -> str:
        funcs = [
            f"{f.get('name')} ({(f.get('docstring') or '').strip().splitlines()[0] if f.get('docstring') else ''})"
            for f in file_metadata.get("functions", [])
            if f.get("name")
        ]
        clss = [
            f"{c.get('name')} ({(c.get('docstring') or '').strip().splitlines()[0] if c.get('docstring') else ''})"
            for c in file_metadata.get("classes", [])
            if c.get("name")
        ]
        docs_hint = (
            (file_metadata.get("docstring") or "").strip().splitlines()[0]
            if file_metadata.get("docstring")
            else ""
        )

        prompt = FILE_COMPACT_SUMMARY_PROMPT.format(
            filepath=file_metadata.get("filepath", "(unknown)"),
            functions=", ".join(funcs) or "(none)",
            classes=", ".join(clss) or "(none)",
            docs=docs_hint or "(none)",
        )
        return self._chat(prompt, system_prompt=SYSTEM_SUMMARY_MESSAGE)

    def generate_file_summary_full(
        self,
        file_metadata: Dict[str, Any],
        component_summaries: Dict[str, Dict[str, str]],
    ) -> str:
        compact = self.generate_file_summary_compact(file_metadata)
        func_summaries = []
        for f in file_metadata.get("functions", []):
            name = f.get("name")
            summ = component_summaries.get("functions", {}).get(name, "")
            if name:
                func_summaries.append(f"- {name}: {summ or '(no summary)'}")

        class_summaries = []
        for c in file_metadata.get("classes", []):
            name = c.get("name")
            summ = component_summaries.get("classes", {}).get(name, "")
            if name:
                class_summaries.append(f"- {name}: {summ or '(no summary)'}")

        prompt = FILE_FULL_SUMMARY_PROMPT.format(
            filepath=file_metadata.get("filepath", "(unknown)"),
            compact=compact,
            function_summaries="\n".join(func_summaries) or "(none)",
            class_summaries="\n".join(class_summaries) or "(none)",
        )
        return self._chat(prompt, system_prompt=SYSTEM_SUMMARY_MESSAGE)

    # ------------------------- Component summaries ------------------------------
    def generate_component_summary(
        self, component_metadata: Dict[str, Any], component_type: str
    ) -> str:
        name = (
            component_metadata.get("name")
            or component_metadata.get("heading")
            or "(unnamed)"
        )
        signature = component_metadata.get("signature") or ""
        doc = (
            component_metadata.get("docstring")
            or component_metadata.get("content")
            or ""
        ).strip()
        related_parts: List[str] = []
        if component_type == "function":
            related_parts = component_metadata.get("calls", [])
        elif component_type == "class":
            related_parts = component_metadata.get("methods", [])
        elif component_type == "markdown_section":
            # summarize code languages present
            langs = {
                b.get("language") or "text"
                for b in component_metadata.get("code_blocks", [])
            }
            related_parts = sorted(list(langs))

        prompt = COMPONENT_SUMMARY_PROMPT.format(
            component_type=component_type,
            name=name,
            signature=signature or "(not provided)",
            docstring=(doc[:1000] + ("..." if len(doc) > 1000 else "")) or "(none)",
            related=", ".join(related_parts) or "(none)",
        )
        return self._chat(prompt, system_prompt=SYSTEM_SUMMARY_MESSAGE)

    def generate_markdown_section_summary(
        self, section_metadata: Dict[str, Any]
    ) -> str:
        section = dict(section_metadata)
        section["name"] = section.get("heading", "(section)")
        return self.generate_component_summary(
            section, component_type="markdown_section"
        )
