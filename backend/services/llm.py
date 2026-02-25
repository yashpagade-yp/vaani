"""
llm.py — Groq LLM Service
===========================
Creates and configures the Groq LLM service for use in the Pipecat pipeline.

What is Groq?
- Groq runs Llama 3 (open-source AI model) on special LPU hardware
- It's MUCH faster than regular GPU servers — critical for voice UX
- The API is OpenAI-compatible, so we use Pipecat's OpenAILLMService
  but point it at Groq's URL instead

Model choice: llama-3.3-70b-versatile
- "70b" = 70 billion parameters — much better reasoning and tool use
- "versatile" = optimized for complex tasks including function calling
- Required for reliable tool calling (8b-instant often misses tool calls)

Free tier: 14,400 requests/day, 6,000 tokens/minute on 70b
"""

from typing import Optional
from pipecat.services.openai.llm import OpenAILLMService
from core.config import settings
from core.logger import logger


def create_llm_service(tools: Optional[list] = None) -> OpenAILLMService:
    """
    Create and return a configured Groq LLM service.

    We use OpenAILLMService because Groq's API is 100% compatible
    with OpenAI's API format — we just change the base_url.

    Args:
        tools: Optional list of tool schemas in OpenAI function-calling format.
               When provided, the LLM gains the ability to call those tools.

    Returns:
        OpenAILLMService: Ready-to-use LLM service for the pipeline

    Usage in pipeline:
        llm = create_llm_service(tools=get_all_tool_schemas())
        pipeline = Pipeline([..., llm, ...])
    """
    logger.info(
        "Creating Groq LLM service | model={} tools={}",
        settings.GROQ_MODEL,
        len(tools) if tools else 0
    )

    return OpenAILLMService(
        # Groq API key from .env
        api_key=settings.GROQ_API_KEY,

        # Point to Groq's API instead of OpenAI's
        # This is the key difference — same format, different server
        base_url="https://api.groq.com/openai/v1",

        # Which model to use (set in .env)
        # Force 70b-versatile as default if .env is missing it, as 8b cannot use tools well
        model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",

        # Tool schemas — tells Groq what tools Vaani has available
        # Empty list means no tools, populated list enables tool calling
        tools=tools or [],
    )
