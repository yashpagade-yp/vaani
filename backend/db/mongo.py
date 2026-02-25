"""
mongo.py — MongoDB Connection Manager
=======================================
Manages the async MongoDB connection using Motor (async MongoDB driver).

Why Motor instead of PyMongo?
- Motor is the ASYNC version of PyMongo
- FastAPI is async, so we need async database calls
- Using sync PyMongo in async FastAPI would BLOCK the server

How it works:
- connect_db() is called once at app startup
- disconnect_db() is called once at app shutdown
- All repositories use the `get_db()` function to get the database object

Usage:
    from db.mongo import get_db
    db = get_db()
    await db["messages"].insert_one({...})
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import settings
from core.logger import logger
from core.exceptions import DatabaseError

# Global client and database objects
# These are set once at startup and reused for all requests
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """
    Connect to MongoDB at app startup.
    Called automatically by FastAPI's startup event in main.py.

    Raises:
        DatabaseError: If connection to MongoDB fails
    """
    global _client, _database

    try:
        logger.info("Connecting to MongoDB at: {}", settings.MONGODB_URI)

        # Create the async MongoDB client
        _client = AsyncIOMotorClient(settings.MONGODB_URI)

        # Get the 'vaani' database (auto-created if it doesn't exist)
        _database = _client.get_default_database()

        # Test the connection by pinging the server
        await _client.admin.command("ping")

        logger.info("[OK] MongoDB connected successfully")

    except Exception as e:
        logger.error("[ERROR] Failed to connect to MongoDB: {}", str(e))
        raise DatabaseError(f"MongoDB connection failed: {str(e)}")


async def disconnect_db() -> None:
    """
    Disconnect from MongoDB at app shutdown.
    Called automatically by FastAPI's shutdown event in main.py.
    """
    global _client, _database

    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("MongoDB disconnected")


def get_db() -> AsyncIOMotorDatabase:
    """
    Get the database object for use in repositories.

    Returns:
        AsyncIOMotorDatabase: The 'vaani' database object

    Raises:
        DatabaseError: If called before connect_db()

    Usage:
        db = get_db()
        await db["messages"].find_one({"session_id": "abc123"})
    """
    if _database is None:
        raise DatabaseError(
            "Database not connected. "
            "Make sure connect_db() was called at app startup."
        )
    return _database
