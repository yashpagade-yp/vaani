"""
webrtc.py — SmallWebRTC Transport Factory
==========================================
Creates the SmallWebRTC transport for a call session.

What is WebRTC?
- WebRTC (Web Real-Time Communication) is a browser technology
  for peer-to-peer audio/video streaming
- It's how the user's voice travels from their browser to our server
  and how the AI's voice travels back

What is SmallWebRTC?
- A lightweight WebRTC implementation built into Pipecat
- No external servers needed (unlike Daily.co which needs their servers)
- Completely free — uses Google's STUN server for NAT traversal
- Perfect for our zero-cost architecture

How it works:
1. Browser sends an SDP "offer" (describes its audio capabilities)
2. Server creates a SmallWebRTCConnection and generates an SDP "answer"
3. Browser and server exchange ICE candidates (find best network path)
4. Audio streams directly between browser and server
"""

from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.base_transport import TransportParams
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from core.logger import logger


def create_transport(webrtc_connection: SmallWebRTCConnection) -> SmallWebRTCTransport:
    """
    Create a SmallWebRTC transport for a call session.

    Args:
        webrtc_connection: The WebRTC connection object created from the
                           browser's SDP offer (done in the /offer route)

    Returns:
        SmallWebRTCTransport: Ready-to-use transport for the pipeline

    Usage:
        connection = SmallWebRTCConnection(sdp_offer)
        transport = create_transport(connection)
        task = build_pipeline(transport, session_id)
    """
    logger.debug("Creating SmallWebRTC transport")

    return SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            # Enable audio input: receive user's voice from browser
            audio_in_enabled=True,
            audio_in_sample_rate=16000,   # Silero VAD requires 16000 or 8000

            # Enable audio output: send AI's voice to browser
            audio_out_enabled=True,
            audio_out_sample_rate=24000,  # Match TTS sample rate (24kHz is high quality)

            # We don't need video for a voice bot
            video_out_enabled=False,

            # VAD: detect when user stops speaking
            # Tuned for faster response (shorter silence timeout)
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    stop_secs=0.5,  # Stop listening after 0.5s silence (was default 0.8s)
                    start_secs=0.2, # Start listening after 0.2s speech
                    confidence=0.5, # Slightly more sensitive
                )
            ),
        )
    )
