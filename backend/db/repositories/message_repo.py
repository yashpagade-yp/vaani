"""
message_repo.py — Chat Message Repository
==========================================
Handles all database operations for chat messages.

The Repository Pattern keeps all MongoDB queries in one place.
Routes and pipeline code NEVER touch MongoDB directly —
they always go through this repository.

Why this pattern?
- Easy to test (you can mock this class in tests)
- If you switch from MongoDB to another DB later,
  you only change this file, nothing else
- Keeps business logic separate from data access logic

Collection name in MongoDB: "messages"
"""

from datetime import datetime
from typing import List, Optional
from db.mongo import get_db
from db.models import Message, MessageRole
from core.logger import logger
from core.exceptions import DatabaseError


# Name of the MongoDB collection where messages are stored
COLLECTION = "messages"


async def save_message(
    session_id: str,
    role: MessageRole,
    content: str
) -> Message:
    """
    Save a new message to the database.

    Args:
        session_id: The call session this message belongs to
        role: Who sent it — "user" or "assistant"
        content: The text content of the message

    Returns:
        Message: The saved message object with auto-generated ID and timestamp

    Example:
        msg = await save_message("sess-123", MessageRole.USER, "Hello!")
        print(msg.id)  # "abc-456"
    """
    try:
        # Create the message object (auto-generates ID and timestamp)
        message = Message(
            session_id=session_id,
            role=role,
            content=content
        )

        # Convert to dict and save to MongoDB
        db = get_db()
        await db[COLLECTION].insert_one(message.model_dump())

        logger.debug(
            "Message saved | session={} role={} chars={}",
            session_id, role, len(content)
        )

        return message

    except Exception as e:
        logger.error("Failed to save message: {}", str(e))
        raise DatabaseError(f"Failed to save message: {str(e)}")


async def get_messages(
    session_id: str,
    limit: int = 50
) -> List[Message]:
    """
    Get all messages for a session, ordered oldest → newest.

    Args:
        session_id: The session to fetch messages for
        limit: Maximum number of messages to return (default: 50)

    Returns:
        List[Message]: List of messages, oldest first

    Example:
        messages = await get_messages("sess-123")
        for msg in messages:
            print(f"{msg.role}: {msg.content}")
    """
    try:
        db = get_db()

        # Find all messages for this session, sorted by timestamp (oldest first)
        cursor = db[COLLECTION].find(
            {"session_id": session_id},
            sort=[("timestamp", 1)],  # 1 = ascending (oldest first)
            limit=limit
        )

        # Convert MongoDB documents to Message objects
        raw_messages = await cursor.to_list(length=limit)
        messages = [Message(**doc) for doc in raw_messages]

        logger.debug(
            "Fetched {} messages for session={}",
            len(messages), session_id
        )

        return messages

    except Exception as e:
        logger.error("Failed to fetch messages: {}", str(e))
        raise DatabaseError(f"Failed to fetch messages: {str(e)}")


async def get_message_count(session_id: str) -> int:
    """
    Count how many messages exist for a session.

    Args:
        session_id: The session to count messages for

    Returns:
        int: Number of messages
    """
    try:
        db = get_db()
        count = await db[COLLECTION].count_documents({"session_id": session_id})
        return count
    except Exception as e:
        raise DatabaseError(f"Failed to count messages: {str(e)}")


async def delete_session_messages(session_id: str) -> int:
    """
    Delete all messages for a session (cleanup).

    Args:
        session_id: The session whose messages to delete

    Returns:
        int: Number of messages deleted
    """
    try:
        db = get_db()
        result = await db[COLLECTION].delete_many({"session_id": session_id})
        logger.info(
            "Deleted {} messages for session={}",
            result.deleted_count, session_id
        )
        return result.deleted_count
    except Exception as e:
        raise DatabaseError(f"Failed to delete messages: {str(e)}")
