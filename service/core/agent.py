"""
Reasoning agent that navigates code context and answers queries.
"""

import json
from typing import Dict, List, Any, Optional
from core.db_manager import DatabaseManager
from utils.constants import SYSTEM_SUMMARY_MESSAGE


class LLMAgent:
    """
    Reasoning agent that navigates code context.

    Attributes:
        llm_client: LLM client
        db_manager: Database manager
        max_iterations: Max tool calls per query
        tools: Available tools
    """

    def __init__(
        self, llm_client, db_manager: DatabaseManager, max_iterations: int = 5
    ) -> None:
        """Initialize agent with tools"""
        self.llm = llm_client
        self.db_manager = db_manager
        self.max_iterations = max_iterations

        # Available tools
        self.tools = {
            "get_related_components": self._get_related_components,
            "trace_execution": self._trace_execution,
            "get_full_file": self._get_full_file,
            "search_components": self._search_components,
            "get_dependency_graph": self._get_dependency_graph,
            "find_component_file": self._find_component_file,
        }

    def answer_query(
        self,
        user_query: str,
        initial_context: Dict[str, Any],
        user_knowledge: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point: answer a user query using reasoning loop.

        Args:
            user_query: "How does authentication work?"
            initial_context: Output from RetrievalEngine
            user_knowledge: UserKnowledge state

        Returns:
        {
            "answer": "Authentication in this project...",
            "sources": [Summary objects used],
            "tools_used": ["get_related_components", "trace_execution"],
            "new_concepts_learned": ["authentication_flow"],
            "confidence": 0.92
        }
        """
        if user_knowledge is None:
            user_knowledge = {"expertise_level": "intermediate", "concepts_learned": []}

        current_context = initial_context.copy()
        tools_used = []
        all_sources = []

        # Start reasoning loop
        for iteration in range(self.max_iterations):
            print(f"    🔄 Iteration {iteration + 1}/{self.max_iterations}")

            # Decide next action
            print("      🤔 Deciding next action...")
            decision = self.decide_next_action(
                user_query, current_context, user_knowledge, iteration
            )
            print(f"      → Action: {decision['action']}")
            if decision.get("reasoning"):
                print(f"      → Reasoning: {decision['reasoning']}")

            if decision["action"] == "answer":
                print("      ✅ Agent decided to answer with current context")
                break

            # Execute tool
            tool_name = decision["tool_name"]
            parameters = decision["parameters"]
            print(f"      🔧 Executing tool: {tool_name} with params: {parameters}")

            try:
                tool_result = self.execute_tool(tool_name, parameters)
                tools_used.append(tool_name)

                if "error" in tool_result:
                    print(f"      ❌ Tool error: {tool_result['error']}")
                else:
                    print("      ✅ Tool executed successfully")
                    if "token_count" in tool_result:
                        print(f"      → Tokens retrieved: {tool_result['token_count']}")

                # Add tool result to context
                if "sources" in tool_result:
                    all_sources.extend(tool_result["sources"])
                    print(f"      → Sources added: {len(tool_result['sources'])}")

                # Merge tool result into current context
                current_context = self._merge_context(current_context, tool_result)

            except Exception as e:
                print(f"      ❌ Tool execution failed: {e}")
                continue

        # Generate final answer
        print("    📝 Generating final answer...")
        answer = self._generate_final_answer(
            user_query, current_context, user_knowledge
        )
        print(f"    ✅ Answer generated ({len(answer)} characters)")

        # Identify learned concepts
        print("    🧠 Identifying learned concepts...")
        new_concepts = self._identify_learned_concepts(user_query, answer)
        if new_concepts:
            print(f"    → New concepts: {new_concepts}")
        else:
            print("    → No new concepts identified")

        return {
            "answer": answer,
            "sources": all_sources,
            "tools_used": tools_used,
            "new_concepts_learned": new_concepts,
            "confidence": 0.85,  # Could be calculated based on source quality
        }

    def decide_next_action(
        self,
        user_query: str,
        current_context: Dict[str, Any],
        user_knowledge: Dict[str, Any],
        iteration: int,
    ) -> Dict[str, Any]:
        """
        Agent decides what to do next.
        """
        # Build context summary
        context_summary = self._summarize_context(current_context)

        prompt = f"""
Given the user query and current context, what should we do next?

Query: {user_query}

Current context:
{context_summary}

User expertise level: {user_knowledge.get("expertise_level", "intermediate")}
Concepts already known: {", ".join(user_knowledge.get("concepts_learned", []))}

Available tools:
- get_related_components: Find functions that call or are called by a component
  Parameters: component_id (string), relationship (string: "calls" or "called_by")
- trace_execution: Follow execution flow from a starting component
  Parameters: component_id (string), max_depth (int, optional, default=3)
- get_full_file: Get complete file summary with all details
  Parameters: filepath (string) - REQUIRES full file path like "/repos/repo_name/file.py"
- search_components: Find components by keyword search
  Parameters: keyword (string), limit (int, optional, default=10)
- get_dependency_graph: Get complete dependency relationships
  Parameters: none
- find_component_file: Find which file contains a specific component
  Parameters: component_name (string)

IMPORTANT: For get_full_file, you MUST first use find_component_file to get the filepath, then use that filepath.

Think about:
1. Does current context answer the query?
2. If not, what's missing?
3. Which tool would be most helpful?

Iteration {iteration + 1} of {self.max_iterations}

Respond in JSON format:
{{
    "action": "tool_name or answer",
    "tool_name": "get_related_components",
    "parameters": {{"component_id": "func_authenticate_user", "relationship": "calls"}},
    "reasoning": "why this action",
    "confidence": 0.85
}}

If you think we have enough context to answer, set action to "answer".
"""

        try:
            response = self.llm.chat.completions.create(
                model="x-ai/grok-code-fast-1",
                messages=[
                    {"role": "system", "content": SYSTEM_SUMMARY_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=300,
            )

            result_text = response.choices[0].message.content.strip()
            decision = json.loads(result_text)

            # Validate action
            if decision["action"] == "answer":
                return decision

            tool_name = decision.get("tool_name")
            if tool_name not in self.tools:
                return {
                    "action": "answer",
                    "reasoning": "Invalid tool",
                    "confidence": 0.0,
                }

            return decision

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return {
                "action": "answer",
                "reasoning": f"Parse error: {e}",
                "confidence": 0.0,
            }
        except Exception as e:
            return {"action": "answer", "reasoning": f"Error: {e}", "confidence": 0.0}

    def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific tool.
        """
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return self.tools[tool_name](parameters)
        except Exception as e:
            return {"error": f"Tool execution failed: {e}"}

    def _get_related_components(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get components related to a target component."""
        component_id = parameters.get("component_id")
        relationship = parameters.get("relationship", "calls")

        if not component_id:
            return {"error": "component_id required"}

        # Get dependencies or dependents
        if relationship == "calls":
            components = self.db_manager.get_dependencies_of_component(
                component_id, "calls"
            )
        elif relationship == "called_by":
            components = self.db_manager.get_dependents_of_component(
                component_id, "calls"
            )
        else:
            components = []

        return {
            "tool": "get_related_components",
            "result": components,
            "sources": components,
            "token_count": sum(c.token_count for c in components),
        }

    def _trace_execution(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Trace execution flow from a component."""
        component_id = parameters.get("component_id")
        max_depth = parameters.get("max_depth", 3)

        if not component_id:
            return {"error": "component_id required"}

        execution_path = self.db_manager.trace_execution_path(component_id, max_depth)

        return {
            "tool": "trace_execution",
            "result": execution_path,
            "sources": execution_path,
            "token_count": sum(s.token_count for s in execution_path),
        }

    def _get_full_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete file summary."""
        filepath = parameters.get("filepath")

        if not filepath:
            return {"error": "filepath required"}

        # Normalize the filepath to match what's stored in the database
        # Remove /repos/inclinet/ prefix if present
        if filepath.startswith("/repos/inclinet/"):
            filepath = filepath[16:]  # Remove "/repos/inclinet/"
        elif filepath.startswith("/repos/"):
            filepath = filepath[7:]  # Remove "/repos/"

        # Remove leading slash if present
        filepath = filepath.lstrip("/")

        file_summary = self.db_manager.get_file_summary(filepath, "full")

        if not file_summary:
            return {"error": f"File not found: {filepath}"}

        return {
            "tool": "get_full_file",
            "result": [file_summary],
            "sources": [file_summary],
            "token_count": file_summary.token_count,
        }

    def _search_components(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for components by keyword."""
        keyword = parameters.get("keyword")
        limit = parameters.get("limit", 10)

        if not keyword:
            return {"error": "keyword required"}

        results = self.db_manager.search_summaries_by_keyword(keyword, limit)

        return {
            "tool": "search_components",
            "result": results,
            "sources": results,
            "token_count": sum(r.token_count for r in results),
        }

    def _get_dependency_graph(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete dependency graph."""
        graph = self.db_manager.get_dependency_graph()

        return {
            "tool": "get_dependency_graph",
            "result": graph,
            "sources": [],
            "token_count": 500,  # Estimate
        }

    def _find_component_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Find which file contains a specific component."""
        component_name = parameters.get("component_name")

        if not component_name:
            return {"error": "component_name required"}

        # Search for the component using multiple strategies
        file_paths = []
        sources = []

        # Strategy 1: Search by component name in summaries
        summary = self.db_manager.search_by_component_name(component_name)
        if summary:
            sources.append(summary)
            # Try to get the file path from the parent_id or target_id
            if hasattr(summary, "parent_id") and summary.parent_id:
                # Convert parent_id (file_id) to filepath
                if summary.parent_id.startswith("file_"):
                    filepath = self._convert_file_id_to_path(summary.parent_id)
                    if filepath:
                        file_paths.append(f"/repos/inclinet/{filepath}")

        # Strategy 2: Search in code mappings
        try:
            # Use search_summaries_by_keyword as a fallback
            keyword_results = self.db_manager.search_summaries_by_keyword(
                component_name, limit=5
            )
            for result in keyword_results:
                if (
                    hasattr(result, "parent_id")
                    and result.parent_id
                    and result.parent_id.startswith("file_")
                ):
                    filepath = self._convert_file_id_to_path(result.parent_id)
                    if filepath:
                        file_paths.append(f"/repos/inclinet/{filepath}")
                        sources.append(result)
        except Exception as e:
            print(f"      Warning: Keyword search failed: {e}")

        # Remove duplicates
        file_paths = list(set(file_paths))

        if not file_paths:
            return {"error": f"No file path found for component '{component_name}'"}

        return {
            "tool": "find_component_file",
            "result": file_paths,
            "sources": sources,
            "token_count": sum(s.token_count for s in sources) if sources else 0,
        }

    def _convert_file_id_to_path(self, file_id: str) -> str:
        """Convert file ID back to file path."""
        if not file_id.startswith("file_"):
            return None

        # Remove "file_" prefix
        path_part = file_id[5:]  # Remove "file_"

        # Convert underscores back to path separators
        # Handle the case where "py" at the end should become ".py"
        if path_part.endswith("_py"):
            path_part = path_part[:-3] + ".py"
        elif path_part.endswith("_md"):
            path_part = path_part[:-3] + ".md"
        elif path_part.endswith("_txt"):
            path_part = path_part[:-4] + ".txt"
        elif path_part.endswith("_json"):
            path_part = path_part[:-5] + ".json"

        # Replace remaining underscores with slashes
        filepath = path_part.replace("_", "/")

        return filepath

    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create a summary of current context for the agent."""
        summary_parts = []

        if context.get("repo_summary"):
            summary_parts.append(f"Repository: {context['repo_summary'].text[:100]}...")

        if context.get("file_summaries"):
            summary_parts.append(
                f"Files: {len(context['file_summaries'])} file summaries"
            )

        if context.get("component_summary"):
            summary_parts.append(f"Component: {context['component_summary'].target_id}")

        if context.get("search_results"):
            summary_parts.append(
                f"Search results: {len(context['search_results'])} matches"
            )

        if context.get("execution_path"):
            summary_parts.append(
                f"Execution path: {len(context['execution_path'])} components"
            )

        if context.get("dependency_graph"):
            summary_parts.append("Dependency graph available")

        if context.get("file_paths"):
            summary_parts.append(f"File paths: {len(context['file_paths'])} files")

        return "\n".join(summary_parts) if summary_parts else "No context available"

    def _merge_context(
        self, current_context: Dict[str, Any], tool_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge tool result into current context."""
        # Simple merging strategy - could be more sophisticated
        merged = current_context.copy()

        if "result" in tool_result:
            if isinstance(tool_result["result"], list):
                # Add to existing lists or create new ones
                for item in tool_result["result"]:
                    if hasattr(item, "level"):
                        level = item.level
                        if level not in merged:
                            merged[level] = []
                        merged[level].append(item)
                    elif isinstance(item, str):
                        # Handle string results (like file paths from find_component_file)
                        if "file_paths" not in merged:
                            merged["file_paths"] = []
                        merged["file_paths"].append(item)

        return merged

    def _generate_final_answer(
        self, user_query: str, context: Dict[str, Any], user_knowledge: Dict[str, Any]
    ) -> str:
        """Generate the final answer based on context."""
        context_summary = self._summarize_context(context)

        prompt = f"""
Answer the user's query based on the available context.

Query: {user_query}

Context:
{context_summary}

User expertise level: {user_knowledge.get("expertise_level", "intermediate")}

Provide a comprehensive, helpful answer. If the context doesn't fully answer the query, 
mention what additional information would be helpful.

Answer:
"""

        try:
            response = self.llm.chat.completions.create(
                model="x-ai/grok-code-fast-1",
                messages=[
                    {"role": "system", "content": SYSTEM_SUMMARY_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=800,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"I apologize, but I encountered an error generating the answer: {e}"

    def _identify_learned_concepts(self, query: str, answer: str) -> List[str]:
        """Identify new concepts the user has learned."""
        prompt = f"""
Extract key technical concepts that the user likely learned from this Q&A.

Query: {query}
Answer: {answer}

Return a JSON list of concept names (2-5 concepts):
["concept1", "concept2", "concept3"]

Focus on:
- Technical terms and patterns
- Architecture concepts
- Implementation details
- Workflow processes

Concepts:
"""

        try:
            response = self.llm.chat.completions.create(
                model="x-ai/grok-code-fast-1",
                messages=[
                    {"role": "system", "content": SYSTEM_SUMMARY_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
            )

            result_text = response.choices[0].message.content.strip()
            concepts = json.loads(result_text)
            return concepts if isinstance(concepts, list) else []

        except Exception:
            return []

    def _adapt_explanation(
        self, explanation: str, user_knowledge: Dict[str, Any]
    ) -> str:
        """
        Adapt explanation based on user's expertise level.
        """
        expertise_level = user_knowledge.get("expertise_level", "intermediate")

        if expertise_level == "beginner":
            # Add more background explanation
            adapted = f"""
{explanation}

Note: This explanation assumes you're new to this topic. If you'd like more technical details 
or have questions about specific implementation aspects, feel free to ask!
"""
        elif expertise_level == "advanced":
            # Focus on implementation details
            adapted = f"""
{explanation}

Technical details: The implementation uses modern patterns and follows best practices. 
If you need specific code examples or architectural decisions, I can provide more details.
"""
        else:
            adapted = explanation

        return adapted
