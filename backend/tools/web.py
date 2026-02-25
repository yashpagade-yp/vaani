"""
web.py — Web Crawl & Extract Tools
=====================================
Two tools that let Vaani read content from specific webpages.

crawl_webpage:   Use Tavily Crawl to explore a full website
                 (follows links, handles JS-rendered pages)

extract_webpage: Use Tavily Extract to get clean text from specific URLs
                 (faster, best for a single well-known page)

Example usage by LLM:
    User: "What does the OpenAI homepage say?"
    LLM calls: extract_webpage(urls=["https://openai.com"])
    Tool returns: clean text from that page
    LLM speaks: "The OpenAI homepage says..."
"""

from tavily import AsyncTavilyClient
from pipecat.processors.frameworks.rtvi import FunctionCallParams

from core.config import settings
from core.logger import logger


# ── Lazy client (shared with search.py's client conceptually, separate instance) ─
_client: AsyncTavilyClient | None = None


def _get_client() -> AsyncTavilyClient:
    """Get or create the Tavily async client (singleton)."""
    global _client
    if _client is None:
        _client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


# ── Crawl Tool Schema ──────────────────────────────────────────────────────────
CRAWL_WEBPAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "crawl_webpage",
        "description": (
            "Crawl a website starting from a given URL, following links to explore multiple pages. "
            "Use this when you need to understand a full website or find information that might "
            "be on linked sub-pages. For a single specific page, use extract_webpage instead."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The starting URL to crawl (e.g., 'https://example.com')"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "How many link levels deep to crawl (1-3). Default is 1.",
                    "default": 1
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of pages to crawl (1-10). Default is 5.",
                    "default": 5
                }
            },
            "required": ["url"]
        }
    }
}


# ── Extract Tool Schema ────────────────────────────────────────────────────────
EXTRACT_WEBPAGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "extract_webpage",
        "description": (
            "Extract clean readable text from one or more specific webpage URLs. "
            "Use this when the user gives you a specific URL and wants to know what it contains. "
            "Faster than crawl_webpage and best for specific known pages."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs to extract content from (max 3 at once)"
                }
            },
            "required": ["urls"]
        }
    }
}


# ── Crawl Handler ──────────────────────────────────────────────────────────────
async def crawl_webpage_handler(params: FunctionCallParams) -> None:
    """Handle a crawl_webpage tool call from the LLM."""
    args = params.arguments
    url = args.get("url", "")
    max_depth = min(int(args.get("max_depth", 1)), 3)   # cap at 3
    limit = min(int(args.get("limit", 5)), 10)           # cap at 10

    logger.info("Tool: crawl_webpage | url='{}' depth={} limit={}", url, max_depth, limit)

    try:
        client = _get_client()
        response = await client.crawl(
            url=url,
            max_depth=max_depth,
            limit=limit,
        )

        pages = response.get("results", [])
        if not pages:
            result = f"No content found when crawling {url}."
        else:
            parts = [f"Crawled {len(pages)} page(s) from {url}:\n"]
            for page in pages:
                page_url = page.get("url", "")
                content = page.get("raw_content", page.get("content", ""))[:500]
                parts.append(f"--- {page_url} ---\n{content}\n")
            result = "\n".join(parts)

        logger.info("Tool: crawl_webpage completed | pages={}", len(pages))

    except Exception as e:
        result = f"Failed to crawl {url}: {str(e)}"
        logger.error("Tool: crawl_webpage error | url='{}' error={}", url, str(e))

    await params.result_callback(result)


# ── Extract Handler ────────────────────────────────────────────────────────────
async def extract_webpage_handler(params: FunctionCallParams) -> None:
    """Handle an extract_webpage tool call from the LLM."""
    args = params.arguments
    urls = args.get("urls", [])[:3]  # cap at 3 URLs

    logger.info("Tool: extract_webpage | urls={}", urls)

    try:
        client = _get_client()
        response = await client.extract(urls=urls)

        extracted = response.get("results", [])
        failed = response.get("failed_results", [])

        if not extracted:
            result = f"Could not extract content from: {', '.join(urls)}"
        else:
            parts = []
            for item in extracted:
                page_url = item.get("url", "")
                raw = item.get("raw_content", "")[:800]  # truncate for LLM context
                parts.append(f"--- Content from {page_url} ---\n{raw}")
            if failed:
                parts.append(f"\nFailed to extract: {', '.join(f['url'] for f in failed)}")
            result = "\n\n".join(parts)

        logger.info("Tool: extract_webpage completed | extracted={} failed={}", len(extracted), len(failed))

    except Exception as e:
        result = f"Failed to extract from URLs: {str(e)}"
        logger.error("Tool: extract_webpage error | urls={} error={}", urls, str(e))

    await params.result_callback(result)
