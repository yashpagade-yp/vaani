"""
models.py — Data Models
========================
Pydantic models define the shape of data stored in MongoDB.
Think of these as blueprints for your data.

Why Pydantic?
- Auto-validates data types (e.g., ensures timestamp is always a datetime)
- Converts between Python objects and JSON automatically
- Gives you IDE autocomplete and type safety
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ── Enums ─────────────────────────────────────────────────────────────────────

class MessageRole(str, Enum):
    """
    Who sent the message?
    - USER: the human speaking/typing
    - ASSISTANT: the AI (Vaani)
    - SYSTEM: internal system messages
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionStatus(str, Enum):
    """
    Current state of a call session.
    - ACTIVE: call is ongoing
    - ENDED: call has finished normally
    - ERROR: call ended due to an error
    """
    ACTIVE = "active"
    ENDED = "ended"
    ERROR = "error"


# ── Message Model ──────────────────────────────────────────────────────────────

class Message(BaseModel):
    """
    Represents a single chat/voice message in a conversation.

    Example document in MongoDB:
    {
        "id": "abc-123",
        "session_id": "sess-456",
        "role": "user",
        "content": "Hello, how are you?",
        "timestamp": "2026-02-18T10:30:00"
    }
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique message ID (auto-generated)"
    )
    session_id: str = Field(
        ...,
        description="Which call session this message belongs to"
    )
    role: MessageRole = Field(
        ...,
        description="Who sent this message: user, assistant, or system"
    )
    content: str = Field(
        ...,
        description="The actual text content of the message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this message was created (UTC)"
    )

    class Config:
        # Allow using enum values directly (e.g., "user" instead of MessageRole.USER)
        use_enum_values = True


# ── Session Model ──────────────────────────────────────────────────────────────

class Session(BaseModel):
    """
    Represents a single voice/chat call session.
    Created when a user starts a call, updated when they hang up.

    Example document in MongoDB:
    {
        "id": "sess-456",
        "started_at": "2026-02-18T10:30:00",
        "ended_at": "2026-02-18T10:35:00",
        "duration_seconds": 300,
        "status": "ended",
        "message_count": 12
    }
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session ID (auto-generated)"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the call started (UTC)"
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="When the call ended (None if still active)"
    )
    duration_seconds: Optional[int] = Field(
        default=None,
        description="Total call duration in seconds (calculated on end)"
    )
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE,
        description="Current status of this session"
    )
    message_count: int = Field(
        default=0,
        description="Total number of messages in this session"
    )

    class Config:
        use_enum_values = True
