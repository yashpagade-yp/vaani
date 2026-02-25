"""
health.py — Health Check Endpoint
===================================
Simple endpoint to verify the server is running.

Why have a health check?
- Load balancers ping /health to know if the server is alive
- You can check it in your browser to confirm the server started
- Shows useful info like active call count

GET /health → { "status": "ok", "active_sessions": 2, "timestamp": "..." }
"""

from datetime import datetime
from fastapi import APIRouter
from transport.session_manager import get_active_count

# Create a router — this is how FastAPI organizes endpoints into groups
# All routes in this file will be prefixed with nothing (root level)
router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns server status and current load.
    Open http://localhost:8000/health in your browser to verify the server is running.
    """
    return {
        "status": "ok",
        "active_sessions": get_active_count(),
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Vaani Voice API",
    }
