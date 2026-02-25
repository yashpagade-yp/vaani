"""
session_manager.py — Active Session Tracker
=============================================
Keeps track of all currently active call sessions in memory.

Why do we need this?
- When a user starts a call, we create a pipeline task
- We need to store that task somewhere so we can:
  a) Cancel it if the user disconnects unexpectedly
  b) Check how many active calls are running
  c) Prevent duplicate sessions for the same session_id

This is an in-memory store (not MongoDB) because:
- Active sessions are temporary — they disappear when the call ends
- We need fast access (no database round-trip)
- MongoDB is for persistent data (chat history, session records)

Note: If you scale to multiple server instances, you'd replace this
with Redis. But for a single server, a dict is perfect.
"""

from typing import Dict
from pipecat.pipeline.task import PipelineTask
from core.logger import logger


# In-memory store: { session_id: PipelineTask }
# This dict holds all currently active call sessions
_active_sessions: Dict[str, PipelineTask] = {}


def add_session(session_id: str, task: PipelineTask) -> None:
    """
    Register a new active session.
    Called when a call starts (in the /offer route).

    Args:
        session_id: Unique ID for this session
        task: The running PipelineTask for this session
    """
    _active_sessions[session_id] = task
    logger.info(
        "Session added | id={} total_active={}",
        session_id, len(_active_sessions)
    )


def remove_session(session_id: str) -> None:
    """
    Remove a session when it ends.
    Called when the call finishes or errors out.

    Args:
        session_id: The session to remove
    """
    if session_id in _active_sessions:
        del _active_sessions[session_id]
        logger.info(
            "Session removed | id={} total_active={}",
            session_id, len(_active_sessions)
        )
    else:
        logger.warning("Tried to remove non-existent session | id={}", session_id)


def get_session(session_id: str) -> PipelineTask | None:
    """
    Get the PipelineTask for a session.

    Args:
        session_id: The session to look up

    Returns:
        PipelineTask if found, None if not active
    """
    return _active_sessions.get(session_id)


def get_active_count() -> int:
    """
    Get the number of currently active call sessions.
    Used by the /health endpoint to show server load.

    Returns:
        int: Number of active sessions
    """
    return len(_active_sessions)


def is_session_active(session_id: str) -> bool:
    """
    Check if a session is currently active.

    Args:
        session_id: The session to check

    Returns:
        bool: True if active, False if not found
    """
    return session_id in _active_sessions
