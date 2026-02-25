"""
time_tool.py — Current Time Tool
===================================
Gives Vaani the ability to tell the current time in any timezone.

Uses Python's datetime — no external API needed.
Supports fuzzy timezone names (e.g., "India", "New York", "London").

Example usage by LLM:
    User: "What time is it in Tokyo?"
    LLM calls: get_current_time(timezone="Asia/Tokyo")
    Tool returns: "Current time in Asia/Tokyo: 11:45 PM, Thursday 19 Feb 2026"
    LLM speaks: "It's 11:45 PM in Tokyo right now."
"""

from datetime import datetime
import zoneinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pipecat.processors.frameworks.rtvi import FunctionCallParams
from core.logger import logger


# ── Common timezone aliases ────────────────────────────────────────────────────
TIMEZONE_ALIASES = {
    # India
    "india": "Asia/Kolkata",
    "ist": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",

    # USA
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "est": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "pst": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "cst": "America/Chicago",

    # Europe
    "london": "Europe/London",
    "gmt": "Europe/London",
    "utc": "UTC",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "cet": "Europe/Paris",

    # Asia
    "tokyo": "Asia/Tokyo",
    "jst": "Asia/Tokyo",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "cst china": "Asia/Shanghai",
    "singapore": "Asia/Singapore",
    "dubai": "Asia/Dubai",

    # Australia
    "sydney": "Australia/Sydney",
    "aest": "Australia/Sydney",

    # Middle East
    "riyadh": "Asia/Riyadh",
    "saudi": "Asia/Riyadh",
}


def _resolve_timezone(tz_name: str) -> ZoneInfo:
    """
    Resolve a timezone string to a ZoneInfo object.
    Supports IANA names (Asia/Kolkata) and common aliases (India, Tokyo, etc.).
    """
    # Try alias first (case-insensitive)
    alias_key = tz_name.lower().strip()
    if alias_key in TIMEZONE_ALIASES:
        tz_name = TIMEZONE_ALIASES[alias_key]

    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        # Try capitalizing (e.g., "asia/kolkata" -> "Asia/Kolkata")
        try:
            parts = tz_name.split("/")
            normalized = "/".join(p.capitalize() for p in parts)
            return ZoneInfo(normalized)
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: '{tz_name}'")


# ── Tool Schema ────────────────────────────────────────────────────────────────
GET_CURRENT_TIME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": (
            "Get the current date and time in any timezone. "
            "Use this whenever the user asks about the current time, date, "
            "or what time it is in a specific city or country."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "Timezone name. Accepts IANA format (e.g., 'Asia/Kolkata', 'America/New_York') "
                        "or common names (e.g., 'India', 'Tokyo', 'London', 'New York', 'UTC'). "
                        "Defaults to 'UTC' if not specified."
                    ),
                    "default": "UTC"
                }
            },
            "required": []
        }
    }
}


# ── Tool Handler ───────────────────────────────────────────────────────────────
async def get_current_time_handler(params: FunctionCallParams) -> None:
    """Handle a get_current_time tool call from the LLM."""
    args = params.arguments
    timezone = args.get("timezone", "UTC").strip()

    logger.info("Tool: get_current_time | timezone='{}'", timezone)

    try:
        tz = _resolve_timezone(timezone)
        now = datetime.now(tz)

        # Format: "3:45 PM, Wednesday 19 February 2026 (IST, UTC+5:30)"
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %d %B %Y")
        tz_abbr = now.strftime("%Z")
        offset = now.strftime("%z")
        # Format offset as +5:30 instead of +0530
        if offset:
            offset_fmt = f"UTC{offset[:3]}:{offset[3:]}"
        else:
            offset_fmt = ""

        result = f"{time_str}, {date_str} ({tz_abbr} {offset_fmt})"
        logger.info("Tool: get_current_time completed | result='{}'", result)

    except ValueError as e:
        result = str(e) + ". Please provide a valid timezone like 'India', 'Tokyo', or 'America/New_York'."
    except Exception as e:
        result = f"Could not get time for '{timezone}': {str(e)}"
        logger.error("Tool: get_current_time error | tz='{}' error={}", timezone, str(e))

    await params.result_callback(result)
