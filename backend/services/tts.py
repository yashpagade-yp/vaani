"""
tts.py — Cartesia Text-to-Speech Service
==========================================
Creates and configures the Cartesia TTS service for use in the Pipecat pipeline.

What is TTS (Text-to-Speech)?
- Converts the AI's text response into audio
- The audio is streamed back to the user's browser via WebRTC
- Cartesia does this in STREAMING mode — sends audio chunks as text is generated
  (doesn't wait for the full response before speaking)

Why Cartesia?
- Pipecat has native CartesiaTTSService — plug and play
- Sonic-3 model: 90ms time-to-first-audio (extremely fast)
- Streaming: audio starts playing before the full sentence is ready
- Natural-sounding voices
- Free tier: 20,000 credits/month

How it fits in the pipeline:
    LLM → [text] → CartesiaTTSService → [audio chunks] → transport.output()
"""

from pipecat.services.cartesia.tts import CartesiaTTSService
from core.config import settings
from core.logger import logger


def create_tts_service() -> CartesiaTTSService:
    """
    Create and return a configured Cartesia TTS service.

    Returns:
        CartesiaTTSService: Ready-to-use TTS service for the pipeline

    Usage in pipeline:
        tts = create_tts_service()
        pipeline = Pipeline([..., tts, transport.output()])
    """
    logger.info(
        "Creating Cartesia TTS service | voice_id={}",
        settings.CARTESIA_VOICE_ID
    )

    return CartesiaTTSService(
        # Cartesia API key from .env
        api_key=settings.CARTESIA_API_KEY,

        # Which voice to use (set in .env)
        # Browse voices at: https://cartesia.ai/voices
        voice_id=settings.CARTESIA_VOICE_ID,

        # Sonic-3 (model="sonic-english") is Cartesia's fastest model
        # 90ms time-to-first-audio — much faster than sonic-2
        model="sonic-english",

        # Output sample rate: 24kHz offers clearer audio than 16kHz
        # We will match this in the transport settings
        sample_rate=24000,
    )
