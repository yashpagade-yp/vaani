"""
search.py — Web Search Tool
============================
Gives Vaani the ability to search the internet in real-time.

Uses Tavily Search API — purpose-built for AI agents.
Returns clean, structured results (not raw HTML).

Example usage by LLM:
    User: "What's the latest news about AI?"
    LLM calls: search_web(query="latest AI news 2025", max_results=3)
    Tool returns: formatted list of results with titles, URLs, summaries
    LLM speaks: "Here's what I found..."
"""

from tavily import AsyncTavilyClient
from pipecat.processors.frameworks.rtvi import FunctionCallParams

from core.config import settings
from core.logger import logger


# ── Lazy client (created on first use) ────────────────────────────────────────
_client: AsyncTavilyClient | None = None


def _get_client() -> AsyncTavilyClient:
    """Get or create the Tavily async client (singleton)."""
    global _client
    if _client is None:
        _client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


# ── Tool Schema (OpenAI function-calling format) ───────────────────────────────
SEARCH_WEB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": (
            "Search the internet for real-time information. "
            "Use this for current events, news, facts, or anything that requires "
            "up-to-date information beyond your training data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific for better results."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-5). Default is 3.",
                    "default": 3
                },
                "search_depth": {
                    "type": "string",
                    "enum": ["basic", "advanced"],
                    "description": "Search depth. Use 'basic' for quick lookups, 'advanced' for comprehensive research.",
                    "default": "basic"
                }
            },
            "required": ["query"]
        }
    }
}


# ── Tool Handler ───────────────────────────────────────────────────────────────
async def search_web_handler(params: FunctionCallParams) -> None:
    """
    Handle a search_web tool call from the LLM.

    Args:
        params: FunctionCallParams containing:
            - arguments: dict with query, max_results, search_depth
            - result_callback: async function to send result back to LLM
    """
    args = params.arguments
    query = args.get("query", "")
    max_results = min(int(args.get("max_results", 3)), 5)  # cap at 5
    search_depth = args.get("search_depth", "basic")

    logger.info("Tool: search_web | query='{}' depth={} n={}", query, search_depth, max_results)

    try:
        client = _get_client()
        response = await client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_answer=True,        # Ask Tavily for an AI-generated summary
        )

        # Format results into a clean string for the LLM
        parts = []

        # If Tavily provides an AI answer, include it first
        if response.get("answer"):
            parts.append(f"Summary: {response['answer']}")

        # Add individual results
        results = response.get("results", [])
        if results:
            parts.append(f"\nTop {len(results)} results:")
            for i, r in enumerate(results, 1):
                title = r.get("title", "No title")
                url = r.get("url", "")
                content = r.get("content", "")[:300]  # truncate long content
                parts.append(f"\n{i}. {title}\n   {url}\n   {content}...")

        result = "\n".join(parts) if parts else "No results found."
        logger.info("Tool: search_web completed | results={}", len(results))

    except Exception as e:
        result = f"Web search failed: {str(e)}. Please try again or answer from your knowledge."
        logger.error("Tool: search_web error | query='{}' error={}", query, str(e))

    await params.result_callback(result)
