"""
tools/__init__.py — Vaani Tool Registry
=========================================
Central registry for all Vaani tools.

Tools available:
    - search_web         → Search the internet (Tavily Search)
    - crawl_webpage      → Crawl a full website (Tavily Crawl)
    - extract_webpage    → Extract text from a URL (Tavily Extract)
    - get_weather        → Live weather for any city (Open-Meteo)
    - calculate          → Math & unit conversions (Python built-in)
    - get_current_time   → Current time in any timezone (Python datetime)

Usage in pipeline/builder.py:
    from tools import get_all_tool_schemas, register_all_tools
    llm = create_llm_service(tools=get_all_tool_schemas())
    register_all_tools(llm)
"""

from tools.search import search_web_handler, SEARCH_WEB_SCHEMA
from tools.web import crawl_webpage_handler, extract_webpage_handler, CRAWL_WEBPAGE_SCHEMA, EXTRACT_WEBPAGE_SCHEMA
from tools.weather import get_weather_handler, GET_WEATHER_SCHEMA
from tools.calculator import calculate_handler, CALCULATE_SCHEMA
from tools.time_tool import get_current_time_handler, GET_CURRENT_TIME_SCHEMA


# ── All tool schemas (sent to LLM so it knows what tools exist) ────────────────
ALL_TOOL_SCHEMAS = [
    SEARCH_WEB_SCHEMA,
    CRAWL_WEBPAGE_SCHEMA,
    EXTRACT_WEBPAGE_SCHEMA,
    GET_WEATHER_SCHEMA,
    CALCULATE_SCHEMA,
    GET_CURRENT_TIME_SCHEMA,
]


def get_all_tool_schemas() -> list[dict]:
    """
    Return all tool schemas in OpenAI function-calling format.
    Pass this to the LLM service so it knows which tools are available.
    """
    return ALL_TOOL_SCHEMAS


def register_all_tools(llm) -> None:
    """
    Register all tool handlers with the Pipecat LLM service.
    The LLM will call these handlers when it decides to use a tool.

    Args:
        llm: The OpenAILLMService instance (Groq in our case)
    """
    llm.register_function("search_web", search_web_handler)
    llm.register_function("crawl_webpage", crawl_webpage_handler)
    llm.register_function("extract_webpage", extract_webpage_handler)
    llm.register_function("get_weather", get_weather_handler)
    llm.register_function("calculate", calculate_handler)
    llm.register_function("get_current_time", get_current_time_handler)


# ── Handler Map (for manual tool execution in routes/chat.py) ────────────────
TOOL_HANDLERS = {
    "search_web": search_web_handler,
    "crawl_webpage": crawl_webpage_handler,
    "extract_webpage": extract_webpage_handler,
    "get_weather": get_weather_handler,
    "calculate": calculate_handler,
    "get_current_time": get_current_time_handler,
}

__all__ = [
    "get_all_tool_schemas",
    "register_all_tools",
    "ALL_TOOL_SCHEMAS",
    "TOOL_HANDLERS",
]
