"""
mongo_tool.py — MCP Chat History Tool
=======================================
An MCP tool that gives the AI access to past conversation history.

Why does the AI need this?
- By default, each call session starts fresh — the AI has no memory
  of previous conversations with the user
- With this tool, the AI can recall past conversations:
  "Last time we talked, you mentioned you were learning Python..."
- This makes the AI feel more personal and context-aware

How it's used:
- The AI calls this tool at the start of a conversation
- It fetches the last N messages from MongoDB
- The AI uses this context to personalize its responses

Note: This is DIFFERENT from the in-session conversation history.
- In-session history: managed automatically by LLMContextAggregator
- Cross-session history: this tool fetches from MongoDB
"""

from typing import List, Optional
from db.mongo import get_db
from core.logger import logger


async def get_chat_history(session_id: str, limit: int = 10) -> dict:
    """
    MCP Tool: Fetch recent chat history for a session from MongoDB.

    Args:
        session_id: The session to fetch history for
        limit: Number of recent messages to fetch (default: 10)

    Returns:
        dict with list of recent messages

    Example return value:
        {
            "session_id": "sess-abc123",
            "message_count": 5,
            "messages": [
                {"role": "user", "content": "Hello!", "timestamp": "..."},
                {"role": "assistant", "content": "Hi there!", "timestamp": "..."},
            ]
        }
    """
    try:
        db = get_db()

        # Fetch recent messages, newest first, then reverse for chronological order
        cursor = db["messages"].find(
            {"session_id": session_id},
            sort=[("timestamp", -1)],  # -1 = descending (newest first)
            limit=limit
        )

        raw_messages = await cursor.to_list(length=limit)

        # Reverse to get chronological order (oldest first)
        raw_messages.reverse()

        # Format for the LLM — simple role/content pairs
        messages = [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": str(msg.get("timestamp", "")),
            }
            for msg in raw_messages
        ]

        return {
            "session_id": session_id,
            "message_count": len(messages),
            "messages": messages,
        }

    except Exception as e:
        logger.error("MCP: Failed to fetch chat history: {}", str(e))
        return {
            "error": f"Failed to fetch chat history: {str(e)}",
            "messages": []
        }


# ── Tool Definition for MCP ───────────────────────────────────────────────────

CHAT_HISTORY_TOOL_DEFINITION = {
    "name": "get_chat_history",
    "description": (
        "Fetch recent chat history for a session from the database. "
        "Use this to recall what was discussed in previous conversations "
        "or earlier in the current session."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The session ID to fetch history for"
            },
            "limit": {
                "type": "integer",
                "description": "Number of recent messages to fetch (default: 10)",
                "default": 10
            }
        },
        "required": ["session_id"]
    },
    "function": get_chat_history,
}
