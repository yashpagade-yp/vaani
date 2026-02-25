"""
config.py — App Configuration
==============================
Loads all environment variables from .env file and validates them.
If any required key is missing, the app will FAIL FAST at startup
instead of crashing later during a live call.

Usage:
    from core.config import settings
    print(settings.GROQ_API_KEY)
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """
    All configuration values for the Vaani backend.
    Values are loaded from the .env file automatically.
    """

    # ── LLM (Groq) ────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = Field(..., description="Groq API key for Llama 3 LLM")
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model name — 70b-versatile is best for tool calling"
    )

    # ── Tools (Tavily) ────────────────────────────────────────────────────────
    TAVILY_API_KEY: str = Field(..., description="Tavily API key for web search, crawl, and extract")

    # ── Speech-to-Text (Deepgram) ──────────────────────────────────────────────
    DEEPGRAM_API_KEY: str = Field(..., description="Deepgram API key for STT")

    # ── Text-to-Speech (Cartesia) ──────────────────────────────────────────────
    CARTESIA_API_KEY: str = Field(..., description="Cartesia API key for TTS")
    CARTESIA_VOICE_ID: str = Field(
        default="a0e99841-438c-4a64-b679-ae501e7d6091",
        description="Cartesia voice ID — change at cartesia.ai/voices"
    )

    # ── Database (MongoDB) ─────────────────────────────────────────────────────
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017/vaani",
        description="MongoDB connection URI"
    )

    # ── WebRTC ────────────────────────────────────────────────────────────────
    STUN_SERVER: str = Field(
        default="stun:stun.l.google.com:19302",
        description="STUN server for WebRTC NAT traversal (Google's free STUN)"
    )

    # ── App Settings ──────────────────────────────────────────────────────────
    APP_HOST: str = Field(default="0.0.0.0", description="Server host")
    APP_PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=True, description="Enable debug mode")

    class Config:
        # Tell Pydantic to read from the .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields in .env without crashing
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Using lru_cache means we only read the .env file once,
    not on every function call.
    """
    return Settings()


# Single global settings object — import this everywhere
settings = get_settings()
