"""
main.py — FastAPI Application Entry Point
==========================================
This is where the entire Vaani backend starts.

What happens when you run `uvicorn main:app`:
1. FastAPI app is created
2. CORS is configured (allows browser to call our API)
3. All routes are registered (/health, /offer, /chat)
4. App starts listening for requests

Startup/Shutdown hooks:
- on_startup: connects to MongoDB before accepting requests
- on_shutdown: disconnects from MongoDB cleanly

To run the server:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Then open:
    http://localhost:8000/health  → check server is running
    http://localhost:8000/docs    → interactive API documentation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logger import logger, setup_logger
from db.mongo import connect_db, disconnect_db
from routes.health import router as health_router
from routes.webrtc import router as webrtc_router
from routes.chat import router as chat_router


# ── Lifespan Manager ──────────────────────────────────────────────────────────
# This handles startup and shutdown events cleanly
# Everything before `yield` runs at startup
# Everything after `yield` runs at shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application lifecycle.
    - Startup: initialize logger, connect to MongoDB
    - Shutdown: disconnect from MongoDB
    """
    # ── STARTUP ───────────────────────────────────────────────────────────────
    setup_logger(debug=settings.DEBUG)
    logger.info("[STARTUP] Vaani backend starting up...")
    logger.info("Debug mode: {}", settings.DEBUG)

    # Connect to MongoDB
    await connect_db()

    logger.info("[READY] Vaani backend ready | http://{}:{}", settings.APP_HOST, settings.APP_PORT)

    yield  # App is running — handle requests

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("🛑 Vaani backend shutting down...")
    await disconnect_db()
    logger.info("Shutdown complete")


# ── Create FastAPI App ────────────────────────────────────────────────────────

app = FastAPI(
    title="Vaani Voice API",
    description=(
        "Zero-cost AI voice and chat backend. "
        "Powered by Pipecat, Groq (Llama 3), Deepgram STT, and Cartesia TTS."
    ),
    version="1.0.0",
    # Attach the lifespan manager for startup/shutdown
    lifespan=lifespan,
    # API docs are available at /docs (Swagger UI)
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) allows the browser to call our API
# Without this, the browser will block requests from a different origin
# (e.g., frontend on localhost:3000 calling backend on localhost:8000)

app.add_middleware(
    CORSMiddleware,
    # In production, replace "*" with your actual frontend URL
    # e.g., allow_origins=["https://vaani.yourdomain.com"]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],   # Allow GET, POST, DELETE, etc.
    allow_headers=["*"],   # Allow all headers
)


# ── Register Routes ───────────────────────────────────────────────────────────
# Each router handles a group of related endpoints

# Health check: GET /health
app.include_router(health_router)

# WebRTC signaling: POST /offer
app.include_router(webrtc_router)

# Chat history: GET/POST/DELETE /chat/{session_id}
app.include_router(chat_router)


# ── Root Endpoint ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """
    Root endpoint — confirms the API is running.
    Open http://localhost:8000/ in your browser.
    """
    return {
        "message": "Vaani Voice API is running",
        "docs": "/docs",
        "health": "/health",
    }
