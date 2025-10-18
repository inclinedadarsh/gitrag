# Prompt and model constants for summarization

# Default OpenRouter model; can be overridden per call
OPENROUTER_MODEL = "x-ai/grok-code-fast-1"

# Optional system prompt to steer the assistant's behavior
SYSTEM_SUMMARY_MESSAGE = (
    "You are a senior software engineer who writes concise, clear summaries. "
    "Prefer plain language over jargon. Avoid hedging. Do not invent APIs or functionality. "
    "If information is missing, infer carefully from names but do not fabricate specifics."
)

REPO_SUMMARY_PROMPT = (
    "Summarize the following Python code repository in 2-3 sentences.\n"
    "Goals:\n"
    "- State what the project does (purpose/use-cases).\n"
    "- Highlight its core components/architecture at a high level.\n"
    "- Mention key technologies and external dependencies.\n\n"
    "Context (structured metadata):\n"
    "Repository name: {repo_name}\n"
    "Modules/Directories: {modules}\n"
    "Key Classes: {classes}\n"
    "Key Functions: {functions}\n"
    "External Dependencies: {dependencies}\n\n"
    "Constraints:\n"
    "- Keep it objective, specific, and non-marketing.\n"
    "- No bullet points; return 1-2 short paragraphs (max ~80 words).\n"
    "- If details are unclear, summarize conservatively.\n\n"
    "Summary:"
)

COMPONENT_SUMMARY_PROMPT = (
    "Summarize this {component_type} in 2-3 sentences.\n\n"
    "Details:\n"
    "- Name: {name}\n"
    "- Signature/Declaration: {signature}\n"
    "- Docstring/Documentation: {docstring}\n"
    "- Related Components (imports/calls/usage): {related}\n\n"
    "Guidance:\n"
    "- Explain what it does, its inputs/outputs (if clear), and why it matters.\n"
    "- Avoid implementation minutiae unless essential to understanding behavior.\n"
    "- Keep within ~60 words.\n\n"
    "Summary:"
)

FILE_COMPACT_SUMMARY_PROMPT = (
    "Summarize this file in ONE sentence (max ~25 words).\n\n"
    "Filepath: {filepath}\n"
    "Functions: {functions}\n"
    "Classes: {classes}\n"
    "Doc Hints: {docs}\n\n"
    "Return only the sentence, no preamble."
)

FILE_FULL_SUMMARY_PROMPT = (
    "Write a short Markdown summary for this file.\n\n"
    "Requirements:\n"
    "- First line: a one-sentence overview.\n"
    "- Then sections for Functions and Classes with concise bullets.\n"
    "- Use provided component summaries verbatim when possible.\n"
    "- Keep total length under ~150 words.\n\n"
    "Context:\n"
    "Filepath: {filepath}\n"
    "Compact Summary: {compact}\n"
    "Function Summaries: {function_summaries}\n"
    "Class Summaries: {class_summaries}\n\n"
    "Return valid Markdown starting with a level-1 heading that contains the filepath."
)

# Query classification patterns
QUERY_PATTERNS = {
    "overview": {
        "patterns": [
            r"what does.*project|repository|codebase.*do",
            r"purpose of.*this",
            r"overview of.*project",
            r"explain the.*project",
            r"describe this.*repository",
            r"^(what|explain|describe|purpose).*\?$",
        ],
        "entry_point": "repository",
        "retrieval": "top-down",
    },
    "component_specific": {
        "patterns": [
            r"how does\s+(\w+)\s+work",
            r"what (?:is|does)\s+(?:the\s+)?(?:function|class|method)\s+(\w+)",
            r"explain\s+(?:function|class|method)\s+(\w+)",
            r"what\s+does\s+(\w+)\s+do",
        ],
        "entry_point": "component",
        "retrieval": "focused",
    },
    "flow_tracing": {
        "patterns": [
            r"(?:trace|follow)\s+(?:the\s+)?(?:execution|flow)\s+(?:of\s+)?(\w+)",
            r"what\s+happens\s+when\s+(\w+)",
            r"trace\s+(?:the\s+)?(?:call\s+)?(?:chain|path|flow)",
            r"(?:step|walk)\s+through\s+(\w+)",
        ],
        "entry_point": "dependency_graph",
        "retrieval": "graph_traversal",
    },
    "location_finding": {
        "patterns": [
            r"where\s+(?:is|can\s+i\s+find)\s+(?:the\s+)?(\w+)",
            r"which\s+file\s+(?:is\s+)?(\w+)\s+in",
            r"find\s+(?:the\s+)?(?:code\s+)?(?:for\s+)?(\w+)",
            r"locate\s+(\w+)",
        ],
        "entry_point": "search",
        "retrieval": "keyword_match",
    },
}

# Query classification prompt with examples
QUERY_CLASSIFICATION_PROMPT = (
    "Classify this user query about a codebase. Use the examples below to understand the patterns:\n\n"
    "EXAMPLES:\n"
    "1. Query: 'What does this project do?'\n"
    "   → Type: overview, Target: null, Confidence: 0.95\n\n"
    "2. Query: 'How does the login function work?'\n"
    "   → Type: component_specific, Target: 'login', Confidence: 0.9\n\n"
    "3. Query: 'Trace the execution flow of authenticate_user'\n"
    "   → Type: flow_tracing, Target: 'authenticate_user', Confidence: 0.9\n\n"
    "4. Query: 'Where is the User class defined?'\n"
    "   → Type: location_finding, Target: 'User', Confidence: 0.9\n\n"
    "5. Query: 'How does backpropagation work in this neural network?'\n"
    "   → Type: component_specific, Target: 'backpropagation', Confidence: 0.85\n\n"
    "6. Query: 'What happens when I call train()?'\n"
    "   → Type: flow_tracing, Target: 'train', Confidence: 0.8\n\n"
    "7. Query: 'How to setup the project locally?'\n"
    "   → Type: overview, Target: null, Confidence: 0.9\n\n"
    "8. Query: 'Explain the loss function'\n"
    "   → Type: component_specific, Target: 'loss', Confidence: 0.9\n\n"
    "CLASSIFICATION RULES:\n"
    "- overview: High-level project understanding, setup instructions, general purpose\n"
    "- component_specific: Specific functions, classes, methods, algorithms\n"
    "- flow_tracing: Execution paths, call chains, what happens when X is called\n"
    "- location_finding: Where to find specific code, file locations\n\n"
    "Query to classify: {user_query}\n\n"
    "Respond in JSON format:\n"
    '{{"type": "overview|component_specific|flow_tracing|location_finding", "target": "component_name_or_null", "confidence": 0.0-1.0}}'
)
