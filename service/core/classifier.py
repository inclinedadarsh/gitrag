"""
Query classification for determining retrieval strategy.
"""

import json
from typing import Dict, List, Optional, Any

from utils.constants import (
    QUERY_PATTERNS,
    QUERY_CLASSIFICATION_PROMPT,
    SYSTEM_SUMMARY_MESSAGE,
)


class QueryClassifier:
    """
    Classifies queries to determine retrieval strategy using LLM with examples.

    Attributes:
        llm_client: LLM for semantic understanding
    """

    def __init__(self, llm_client) -> None:
        """Initialize with LLM client"""
        self.llm = llm_client
        self.query_patterns = QUERY_PATTERNS

    def classify_query(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Classify a user query and determine retrieval strategy.

        Args:
            user_query: "How does authentication work?"
            conversation_history: Previous turns for context

        Returns:
        {
            "type": "flow_tracing",
            "entry_point": "dependency_graph",
            "target": "func_login_endpoint",
            "retrieval_strategy": "graph_traversal",
            "needs_code": True,
            "needs_full_context": False,
            "confidence": 0.95
        }
        """
        # Use LLM for classification with examples
        classification = self._classify_with_llm(user_query)

        # Determine additional metadata
        classification.update(self._determine_metadata(classification))

        return classification

    def _classify_with_llm(self, user_query: str) -> Dict[str, Any]:
        """
        Classify query using LLM with examples.
        """
        try:
            prompt = QUERY_CLASSIFICATION_PROMPT.format(user_query=user_query)

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

            # Parse JSON response
            try:
                result = json.loads(result_text)
                query_type = result.get("type", "overview")
                target = result.get("target")
                confidence = float(result.get("confidence", 0.5))

                # Map to our internal structure
                config = self.query_patterns.get(
                    query_type, self.query_patterns["overview"]
                )

                return {
                    "type": query_type,
                    "entry_point": config["entry_point"],
                    "retrieval_strategy": config["retrieval"],
                    "target": target,
                    "confidence": confidence,
                }

            except (json.JSONDecodeError, KeyError, ValueError):
                # Fallback if JSON parsing fails
                return {
                    "type": "overview",
                    "entry_point": "repository",
                    "retrieval_strategy": "top-down",
                    "target": None,
                    "confidence": 0.4,
                }

        except Exception:
            # Fallback if LLM call fails
            return {
                "type": "overview",
                "entry_point": "repository",
                "retrieval_strategy": "top-down",
                "target": None,
                "confidence": 0.2,
            }

    def _determine_metadata(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine additional metadata based on classification.
        """
        query_type = classification["type"]

        # Determine if code is needed
        needs_code = query_type in [
            "component_specific",
            "flow_tracing",
            "location_finding",
        ]

        # Determine if full context is needed
        needs_full_context = query_type in ["overview", "flow_tracing"]

        # Determine priority level
        priority = "high" if query_type == "location_finding" else "medium"

        return {
            "needs_code": needs_code,
            "needs_full_context": needs_full_context,
            "priority": priority,
            "estimated_tokens": self._estimate_token_usage(classification),
        }

    def _estimate_token_usage(self, classification: Dict[str, Any]) -> int:
        """
        Estimate token usage for the retrieval strategy.
        """
        query_type = classification["type"]

        # Rough estimates based on query type
        estimates = {
            "overview": 500,  # Repository summary + file summaries
            "component_specific": 200,  # Single component + context
            "flow_tracing": 800,  # Multiple components in chain
            "location_finding": 100,  # Just location info
        }

        return estimates.get(query_type, 300)

    def get_retrieval_plan(self, classification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed retrieval plan based on classification.

        Returns:
        {
            "steps": [
                {"action": "get_repository_summary", "params": {}},
                {"action": "search_by_keyword", "params": {"keyword": "auth"}}
            ],
            "expected_results": "repository_summary + matching_components",
            "fallback_strategy": "broad_search"
        }
        """
        query_type = classification["type"]
        target = classification.get("target")

        if query_type == "overview":
            return {
                "steps": [
                    {"action": "get_repository_summary", "params": {}},
                    {"action": "get_all_file_summaries", "params": {}},
                ],
                "expected_results": "repository_summary + file_summaries",
                "fallback_strategy": "keyword_search",
            }

        elif query_type == "component_specific":
            if target:
                return {
                    "steps": [
                        {
                            "action": "search_by_component_name",
                            "params": {"name": target},
                        },
                        {
                            "action": "get_component_summary_with_code",
                            "params": {"summary_id": f"func_{target}"},
                        },
                    ],
                    "expected_results": "component_summary + code_location",
                    "fallback_strategy": "keyword_search",
                }
            else:
                return {
                    "steps": [
                        {
                            "action": "search_summaries_by_keyword",
                            "params": {"keyword": "component"},
                        }
                    ],
                    "expected_results": "matching_components",
                    "fallback_strategy": "broad_search",
                }

        elif query_type == "flow_tracing":
            if target:
                return {
                    "steps": [
                        {
                            "action": "trace_execution_path",
                            "params": {
                                "start_component_id": f"func_{target}",
                                "max_depth": 5,
                            },
                        },
                        {
                            "action": "get_dependencies_of_component",
                            "params": {
                                "summary_id": f"func_{target}",
                                "relationship": "calls",
                            },
                        },
                    ],
                    "expected_results": "execution_chain + dependencies",
                    "fallback_strategy": "dependency_graph_search",
                }
            else:
                return {
                    "steps": [{"action": "get_dependency_graph", "params": {}}],
                    "expected_results": "complete_dependency_graph",
                    "fallback_strategy": "file_based_search",
                }

        elif query_type == "location_finding":
            if target:
                return {
                    "steps": [
                        {
                            "action": "search_by_component_name",
                            "params": {"name": target},
                        },
                        {
                            "action": "get_component_summary_with_code",
                            "params": {"summary_id": f"func_{target}"},
                        },
                    ],
                    "expected_results": "code_location + context",
                    "fallback_strategy": "file_search",
                }
            else:
                return {
                    "steps": [
                        {
                            "action": "search_summaries_by_keyword",
                            "params": {"keyword": "location"},
                        }
                    ],
                    "expected_results": "matching_locations",
                    "fallback_strategy": "directory_search",
                }

        # Default fallback
        return {
            "steps": [
                {
                    "action": "search_summaries_by_keyword",
                    "params": {"keyword": "general"},
                }
            ],
            "expected_results": "general_matches",
            "fallback_strategy": "broad_search",
        }
