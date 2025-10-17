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
