"""
datetime_tool.py — MCP DateTime Tool
=======================================
An MCP tool that gives the AI access to the current date and time.

Why does the AI need this?
- LLMs are trained on data up to a cutoff date
- They don't know what time it is right now
- With this tool, the AI can answer "What time is it?" accurately
- It can also be time-aware in conversations ("Good morning!", "Happy Friday!")

How MCP tools work:
1. The tool is registered with the MCP server
2. The LLM sees the tool in its "available tools" list
3. When the LLM decides to use it, it calls the tool
4. The tool returns the result to the LLM
5. The LLM uses the result in its response

This is called "function calling" or "tool use" in LLM terminology.
"""

from datetime import datetime
import pytz


def get_current_datetime(timezone: str = "Asia/Kolkata") -> dict:
    """
    MCP Tool: Get the current date and time.

    This function is registered as an MCP tool so the AI can call it
    whenever it needs to know the current time.

    Args:
        timezone: Timezone name (default: Asia/Kolkata = IST)
                  Other examples: "UTC", "America/New_York", "Europe/London"

    Returns:
        dict with current date, time, day, and timezone info

    Example return value:
        {
            "date": "2026-02-18",
            "time": "16:45:30",
            "day_of_week": "Wednesday",
            "timezone": "Asia/Kolkata",
            "formatted": "Wednesday, February 18, 2026 at 4:45 PM IST"
        }
    """
    try:
        # Get the timezone object
        tz = pytz.timezone(timezone)

        # Get current time in the specified timezone
        now = datetime.now(tz)

        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "month": now.strftime("%B"),
            "year": now.year,
            "timezone": timezone,
            # Human-friendly format for the AI to use in responses
            "formatted": now.strftime("%A, %B %d, %Y at %I:%M %p %Z"),
        }

    except Exception as e:
        return {
            "error": f"Failed to get datetime: {str(e)}",
            "fallback": datetime.utcnow().isoformat() + " UTC"
        }


# ── Tool Definition for MCP ───────────────────────────────────────────────────
# This dict describes the tool to the MCP server
# The LLM reads this description to know when and how to use the tool

DATETIME_TOOL_DEFINITION = {
    "name": "get_current_datetime",
    "description": (
        "Get the current date and time. "
        "Use this when the user asks about the current time, date, day of week, "
        "or when you need to be time-aware in your response."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "Timezone name (e.g., 'Asia/Kolkata', 'UTC', 'America/New_York')",
                "default": "Asia/Kolkata"
            }
        },
        "required": []
    },
    # The actual function to call
    "function": get_current_datetime,
}
