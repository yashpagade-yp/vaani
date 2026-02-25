"""
test_health.py — Health Endpoint Tests
========================================
Basic smoke tests to verify the server is running correctly.

Run with:
    cd vaani/backend
    pytest tests/ -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

# We patch the database so tests don't need a real MongoDB connection
@pytest.fixture
def mock_db():
    """Mock the database connection so tests run without MongoDB."""
    with patch("db.mongo.connect_db", new_callable=AsyncMock):
        with patch("db.mongo.disconnect_db", new_callable=AsyncMock):
            with patch("transport.session_manager.get_active_count", return_value=0):
                yield


@pytest.mark.asyncio
async def test_health_check(mock_db):
    """
    Test that GET /health returns 200 OK with correct fields.
    This is the most basic test — if this fails, the server is broken.
    """
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "active_sessions" in data
    assert "timestamp" in data
    assert data["service"] == "Vaani Voice API"


@pytest.mark.asyncio
async def test_root_endpoint(mock_db):
    """
    Test that GET / returns the welcome message.
    """
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "Vaani" in data["message"]
