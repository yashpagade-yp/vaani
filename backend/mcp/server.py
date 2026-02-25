"""
server.py — MCP Server Entry Point
=====================================
Sets up and runs the MCP (Model Context Protocol) server.

What is MCP?
- MCP is a standard protocol for giving AI models access to external tools
- Think of it as a "plugin system" for AI
- The AI can call tools to get real-world data (time, database, etc.)
- This makes the AI more capable and context-aware

Our MCP tools:
1. get_current_datetime → AI knows what time it is
2. get_chat_history    → AI can recall past conversations

How it integrates with Pipecat:
- Pipecat's OpenAILLMService supports function calling
- We register our tools as functions the LLM can call
- When the LLM decides to use a tool, Pipecat handles the call automatically

Reference: https://daily-docs.mcp.kapa.ai
"""

from mcp.tools.datetime_tool import DATETIME_TOOL_DEFINITION, get_current_datetime
from mcp.tools.mongo_tool import CHAT_HISTORY_TOOL_DEFINITION, get_chat_history
from core.logger import logger


# ── All Available MCP Tools ───────────────────────────────────────────────────
# Add new tools here as you build them

ALL_TOOLS = [
    DATETIME_TOOL_DEFINITION,
    CHAT_HISTORY_TOOL_DEFINITION,
]


def get_tool_definitions() -> list[dict]:
    """
    Get all MCP tool definitions for registering with the LLM.

    Returns the list of tool schemas that tell the LLM:
    - What tools are available
    - What each tool does
    - What parameters each tool accepts

    Usage in pipeline/builder.py:
        from mcp.server import get_tool_definitions
        tools = get_tool_definitions()
        llm = OpenAILLMService(..., tools=tools)
    """
    # Return only the schema part (not the function reference)
    # The LLM sees the schema; we handle the actual function calls
    schemas = []
    for tool in ALL_TOOLS:
        schema = {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        }
        schemas.append(schema)

    logger.debug("MCP: {} tools available", len(schemas))
    return schemas


async def call_tool(tool_name: str, tool_args: dict) -> str:
    """
    Execute an MCP tool by name and return the result as a string.

    This is called by the pipeline when the LLM decides to use a tool.
    The result is fed back to the LLM so it can incorporate it in its response.

    Args:
        tool_name: Name of the tool to call (e.g., "get_current_datetime")
        tool_args: Arguments to pass to the tool

    Returns:
        str: Tool result as a string (LLM reads this)

    Example:
        result = await call_tool("get_current_datetime", {"timezone": "Asia/Kolkata"})
        # Returns: "Wednesday, February 18, 2026 at 4:45 PM IST"
    """
    logger.info("MCP tool called | name={} args={}", tool_name, tool_args)

    # Find the tool by name
    tool = next((t for t in ALL_TOOLS if t["name"] == tool_name), None)

    if not tool:
        error_msg = f"Unknown tool: {tool_name}"
        logger.error("MCP: {}", error_msg)
        return error_msg

    try:
        # Call the tool function
        func = tool["function"]

        # Check if it's async (like mongo_tool) or sync (like datetime_tool)
        import asyncio
        if asyncio.iscoroutinefunction(func):
            result = await func(**tool_args)
        else:
            result = func(**tool_args)

        # Convert result to string for the LLM
        import json
        result_str = json.dumps(result, default=str)

        logger.info("MCP tool result | name={} result_length={}", tool_name, len(result_str))
        return result_str

    except Exception as e:
        error_msg = f"Tool {tool_name} failed: {str(e)}"
        logger.error("MCP: {}", error_msg)
        return error_msg
