"""
stt.py — Deepgram Speech-to-Text Service
==========================================
Creates and configures the Deepgram STT service for use in the Pipecat pipeline.

What is STT (Speech-to-Text)?
- Converts the user's voice (audio) into text
- The text is then sent to the LLM (Groq) for processing
- Deepgram does this in REAL-TIME (streaming) — word by word as you speak

Why Deepgram?
- Pipecat has native DeepgramSTTService — plug and play
- Nova-2 model: best accuracy for conversational speech
- Streaming transcription: very low latency
- Free tier: 45,000 minutes/year

How it fits in the pipeline:
    transport.input() → [audio] → DeepgramSTTService → [text] → LLM
"""

from pipecat.services.deepgram.stt import DeepgramSTTService
from deepgram import LiveOptions
from core.config import settings
from core.logger import logger


def create_stt_service() -> DeepgramSTTService:
    """
    Create and return a configured Deepgram STT service.

    Returns:
        DeepgramSTTService: Ready-to-use STT service for the pipeline

    Usage in pipeline:
        stt = create_stt_service()
        pipeline = Pipeline([transport.input(), stt, ...])
    """
    logger.info("Creating Deepgram STT service | model=nova-2")

    return DeepgramSTTService(
        # Deepgram API key from .env
        api_key=settings.DEEPGRAM_API_KEY,

        # Deepgram live transcription options
        live_options=LiveOptions(
            # nova-2 is Deepgram's best model for conversational speech
            model="nova-2",

            # Language: English
            language="en-US",

            # Smart formatting: adds punctuation, capitalizes sentences
            smart_format=True,

            # Endpointing: detects when the user stops speaking
            # 300ms of silence = end of utterance
            # This is what triggers the AI to respond
            endpointing=300,

            # Interim results: send partial transcripts as user speaks
            # This makes the pipeline feel more responsive
            interim_results=True,

            # Utterance end: additional signal for end of speech
            utterance_end_ms="1000",
        )
    )
