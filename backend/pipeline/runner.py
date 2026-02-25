"""
runner.py — Pipeline Runner & Event Handlers
=============================================
Manages the lifecycle of a Pipecat pipeline for one call session.

Lifecycle of a call:
1. Browser connects → on_client_connected fires
2. Browser signals ready → on_client_ready fires → AI says greeting
3. Conversation happens (pipeline runs automatically)
4. Browser disconnects → on_client_disconnected fires → cleanup

Event handlers are how Pipecat tells us what's happening:
- on_client_connected: a browser just joined the call
- on_client_ready: browser finished WebRTC setup, ready for audio
- on_client_disconnected: browser left (user hung up or lost connection)
"""

from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.frames.frames import LLMMessagesFrame
from pipecat.transports.base_transport import BaseTransport

from db.repositories import session_repo, message_repo
from db.models import SessionStatus
from pipeline.prompts import VAANI_GREETING
from core.logger import logger


async def run_pipeline(
    task: PipelineTask,
    transport: BaseTransport,
    session_id: str
) -> None:
    """
    Run the pipeline for one call session with proper event handling.

    This function:
    1. Registers event handlers (connect, ready, disconnect)
    2. Creates a session record in MongoDB
    3. Starts the pipeline runner (blocks until call ends)
    4. Cleans up when the call ends

    Args:
        task: The PipelineTask built by builder.py
        transport: The SmallWebRTC transport for this session
        session_id: Unique ID for this session

    Note:
        This is called as an asyncio background task from the /offer route.
        It runs for the entire duration of the call.
    """

    # ── Event Handler: Client Connected ───────────────────────────────────────
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """
        Fires when the browser successfully connects via WebRTC.
        At this point, audio can flow but the client may not be ready yet.
        """
        logger.info("Client connected | session={}", session_id)

        # Create a session record in MongoDB
        await session_repo.create_session(session_id)

    # ── Event Handler: Client Ready ───────────────────────────────────────────
    @transport.event_handler("on_client_ready")
    async def on_client_ready(transport, client):
        """
        Fires when the browser signals it's ready for the conversation.
        This is when we kick off the AI's opening greeting.

        We send a special message to the LLM telling it to greet the user.
        The LLM generates the greeting → TTS speaks it → user hears it.
        """
        logger.info("Client ready — starting conversation | session={}", session_id)

        # Send the greeting instruction to the LLM
        # This triggers the AI to introduce itself
        await task.queue_frames([
            LLMMessagesFrame([
                {
                    "role": "user",
                    "content": "Please greet the user warmly and introduce yourself briefly.",
                }
            ])
        ])

    # ── Event Handler: Client Disconnected ────────────────────────────────────
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """
        Fires when the browser disconnects (user hangs up or loses connection).
        We cancel the pipeline and update the session in MongoDB.
        """
        logger.info("Client disconnected | session={}", session_id)

        # Cancel the pipeline — stops all AI processing
        await task.cancel()

        # Mark the session as ended in MongoDB (calculates duration automatically)
        await session_repo.end_session(session_id, SessionStatus.ENDED)

        logger.info("Session ended cleanly | session={}", session_id)

    # ── Run the Pipeline ───────────────────────────────────────────────────────
    # PipelineRunner manages the pipeline execution
    # handle_sigint=False: let FastAPI handle shutdown signals, not the runner
    runner = PipelineRunner(handle_sigint=False)

    try:
        logger.info("Pipeline runner starting | session={}", session_id)
        # This blocks until the pipeline finishes (call ends)
        await runner.run(task)
    except Exception as e:
        logger.error("Pipeline error | session={} error={}", session_id, str(e))
        # Mark session as errored in MongoDB
        await session_repo.end_session(session_id, SessionStatus.ERROR)
        raise
    finally:
        logger.info("Pipeline runner finished | session={}", session_id)
