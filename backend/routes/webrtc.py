"""
webrtc.py — WebRTC Signaling Route
=====================================
The most important route in the entire backend.

This is where a voice call begins:
1. Browser records user clicking "Start Call"
2. Browser creates an SDP offer (describes its audio capabilities)
3. Browser sends the offer to POST /offer
4. We create a WebRTC connection and start the AI pipeline
5. We send back an SDP answer
6. Browser and server complete the WebRTC handshake
7. Audio starts flowing — the call is live!

What is SDP?
- Session Description Protocol
- A text format that describes audio/video capabilities
- "I can send/receive audio at 48kHz, using Opus codec..."
- Browser sends an "offer", server sends an "answer"

POST /offer
    Body: { "sdp": "...", "type": "offer" }
    Response: { "sdp": "...", "type": "answer", "session_id": "..." }
"""

import asyncio
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from transport.webrtc import create_transport
from transport.session_manager import add_session, remove_session
from pipeline.builder import build_pipeline
from pipeline.runner import run_pipeline
from core.logger import logger
from core.exceptions import WebRTCError, PipelineError

router = APIRouter(tags=["WebRTC"])


# ── Request/Response Models ────────────────────────────────────────────────────

class SDPOffer(BaseModel):
    """
    The SDP offer sent by the browser when starting a call.
    The browser generates this automatically using the WebRTC API.
    """
    sdp: str          # Session Description Protocol string
    type: str         # Always "offer" for the initial request


class SDPAnswer(BaseModel):
    """
    The SDP answer we send back to the browser.
    After receiving this, the browser completes the WebRTC handshake.
    """
    sdp: str          # Our answer SDP string
    type: str         # Always "answer"
    session_id: str   # Unique ID for this call session


# ── Route ──────────────────────────────────────────────────────────────────────

@router.post("/offer", response_model=SDPAnswer)
async def webrtc_offer(offer: SDPOffer):
    """
    Handle a WebRTC offer from the browser to start a voice call.

    This endpoint:
    1. Receives the browser's SDP offer
    2. Creates a SmallWebRTC connection
    3. Generates a unique session ID
    4. Builds the AI pipeline (STT → LLM → TTS)
    5. Starts the pipeline in the background (non-blocking)
    6. Returns the SDP answer to the browser

    The pipeline runs as a background task — this endpoint returns
    immediately without waiting for the call to end.
    """
    # Generate a unique ID for this call session
    session_id = str(uuid.uuid4())

    logger.info("New call request | session={}", session_id)

    try:
        # ── Step 1: Create WebRTC Connection ──────────────────────────────────
        # SmallWebRTCConnection handles the WebRTC protocol details
        # It takes the browser's offer and prepares an answer
        webrtc_connection = SmallWebRTCConnection()

        # Process the browser's SDP offer
        # This negotiates audio codecs, network paths, etc.
        await webrtc_connection.initialize(
            sdp=offer.sdp,
            type=offer.type
        )

        # Get the SDP answer to send back to the browser
        answer = webrtc_connection.get_answer()

        # ── Step 2: Build the AI Pipeline ─────────────────────────────────────
        # Create the SmallWebRTC transport (wraps the connection)
        transport = create_transport(webrtc_connection)

        # Build the full pipeline: STT → LLM → TTS
        task = build_pipeline(transport, session_id)

        # ── Step 3: Track the Session ─────────────────────────────────────────
        # Store the task so we can cancel it if needed
        add_session(session_id, task)

        # ── Step 4: Start Pipeline in Background ──────────────────────────────
        # asyncio.create_task() runs the pipeline WITHOUT blocking this endpoint
        # The call runs in the background while we return the answer immediately
        async def run_and_cleanup():
            """Run the pipeline and clean up when done."""
            try:
                await run_pipeline(task, transport, session_id)
            finally:
                # Always remove the session when done, even if it crashed
                remove_session(session_id)

        asyncio.create_task(run_and_cleanup())

        logger.info("Call started | session={}", session_id)

        # ── Step 5: Return SDP Answer ──────────────────────────────────────────
        # Browser receives this and completes the WebRTC handshake
        return SDPAnswer(
            sdp=answer["sdp"],
            type=answer["type"],
            session_id=session_id
        )

    except WebRTCError as e:
        logger.error("WebRTC error | session={} error={}", session_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except PipelineError as e:
        logger.error("Pipeline error | session={} error={}", session_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in /offer | session={} error={}", session_id, str(e))
        raise HTTPException(status_code=500, detail="Failed to start call")
