"""
exceptions.py — Custom Exception Classes
==========================================
Defines app-specific exceptions so we can catch and handle
errors precisely instead of catching generic Exception everywhere.

Usage:
    from core.exceptions import PipelineError, WebRTCError, DatabaseError

    raise PipelineError("Failed to build pipeline for session abc123")
"""


class VaaniBaseError(Exception):
    """
    Base class for all Vaani custom exceptions.
    All other custom exceptions inherit from this.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"[{self.__class__.__name__}] {self.message}"


class PipelineError(VaaniBaseError):
    """
    Raised when something goes wrong with the Pipecat pipeline.
    Examples:
        - Failed to build the STT → LLM → TTS pipeline
        - Pipeline task crashed unexpectedly
    """
    pass


class WebRTCError(VaaniBaseError):
    """
    Raised when something goes wrong with WebRTC signaling.
    Examples:
        - Invalid SDP offer from browser
        - Failed to create SmallWebRTC connection
    """
    pass


class DatabaseError(VaaniBaseError):
    """
    Raised when a MongoDB operation fails.
    Examples:
        - Cannot connect to MongoDB
        - Failed to save a chat message
    """
    pass


class ServiceError(VaaniBaseError):
    """
    Raised when an external AI service (Groq, Deepgram, Cartesia) fails.
    Examples:
        - Groq API rate limit exceeded
        - Deepgram connection dropped
        - Cartesia TTS returned an error
    """
    pass


class ConfigError(VaaniBaseError):
    """
    Raised when required configuration is missing or invalid.
    Examples:
        - GROQ_API_KEY not set in .env
        - Invalid CARTESIA_VOICE_ID format
    """
    pass
