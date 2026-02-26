"""
llm.py — Groq LLM Service
===========================
Creates and configures the Groq LLM service for use in the Pipecat pipeline.

What is Groq?
- Groq runs Llama 3 (open-source AI model) on special LPU hardware
- It's MUCH faster than regular GPU servers — critical for voice UX
- The API is OpenAI-compatible, so we use Pipecat's OpenAILLMService
  but point it at Groq's URL instead

Model strategy:
- llama-3.1-8b-instant: for tool calling (correct JSON format)
- llama-3.3-70b-versatile: for general conversation without tools
  (3.3-70b has a bug where it generates XML tool calls instead of JSON)

Free tier: 14,400 requests/day, 6,000 tokens/minute on 70b
"""

from typing import Optional
from pipecat.services.openai.llm import OpenAILLMService
from core.config import settings
from core.logger import logger

# Model that reliably handles tool calling (correct JSON format)
VOICE_TOOL_MODEL = "llama-3.1-8b-instant"


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
    """
    # Use 8b-instant when tools are enabled (correct JSON tool format)
    # Use 70b-versatile when no tools (better conversation quality)
    if tools:
        model = VOICE_TOOL_MODEL
    else:
        model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"

    logger.info(
        "Creating Groq LLM service | model={} tools={}",
        model,
        len(tools) if tools else 0
    )

    return OpenAILLMService(
        # Groq API key from .env
        api_key=settings.GROQ_API_KEY,

        # Point to Groq's API instead of OpenAI's
        base_url="https://api.groq.com/openai/v1",

        # Model selection based on whether tools are needed
        model=model,

        # Tool schemas — tells Groq what tools Vaani has available
        tools=tools or [],
    )
