"""
test_config.py — Configuration Tests
=======================================
Tests that the configuration loads correctly from .env.
"""

import pytest


def test_config_loads():
    """
    Test that settings load without errors.
    If any required key is missing from .env, this test will fail.
    """
    from core.config import settings

    # All these should be set (not empty)
    assert settings.GROQ_API_KEY, "GROQ_API_KEY is missing from .env"
    assert settings.DEEPGRAM_API_KEY, "DEEPGRAM_API_KEY is missing from .env"
    assert settings.CARTESIA_API_KEY, "CARTESIA_API_KEY is missing from .env"
    assert settings.MONGODB_URI, "MONGODB_URI is missing from .env"

    # Check defaults
    assert settings.APP_PORT == 8000
    assert settings.GROQ_MODEL == "llama-3.1-8b-instant"


def test_mcp_datetime_tool():
    """
    Test that the MCP datetime tool returns correct structure.
    This test doesn't need a database or API keys.
    """
    from mcp.tools.datetime_tool import get_current_datetime

    result = get_current_datetime("Asia/Kolkata")

    assert "date" in result
    assert "time" in result
    assert "day_of_week" in result
    assert "formatted" in result
    assert "error" not in result
