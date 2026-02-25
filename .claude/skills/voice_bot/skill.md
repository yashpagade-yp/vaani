---
name: voice-bot
description: Build and work with the Vaani AI voice + chat web application. Use this skill when the user asks about building the Pipecat pipeline, WebRTC signaling, FastAPI backend, STT/TTS/LLM service integration, MongoDB chat history, or any backend component of the Vaani voice bot project.
---

# Voice Bot — Vaani Project Skill

## Project Context

Vaani is a **zero-cost, real-time AI voice + chat web app** built with:

| Component | Technology |
|-----------|-----------|
| Pipeline Framework | Pipecat (`pipecat-ai[webrtc]`) |
| Transport | SmallWebRTC (P2P, no paid infra) |
| Backend API | FastAPI + Uvicorn (Python async) |
| LLM | Groq — Llama 3.1 8B (`llama-3.1-8b-instant`) |
| STT | Deepgram (`DeepgramSTTService`) |
| TTS | Cartesia (`CartesiaTTSService`) |
| Database | MongoDB Atlas M0 (free) + Motor async driver |
| Client SDK | `@pipecat-ai/client-js` (browser) |
| STUN | `stun:stun.l.google.com:19302` (free) |

**Cost target: $0** — all services use free tiers only.

---

## Project Structure

```
vaani/
├── backend/
│   ├── main.py          # FastAPI app, startup, CORS
│   ├── pipeline.py      # Pipecat pipeline definition
│   ├── routes/
│   │   ├── webrtc.py    # POST /offer — SDP signaling
│   │   ├── chat.py      # GET/POST /chat — history
│   │   └── health.py    # GET /health
│   ├── services/
│   │   ├── llm.py       # Groq LLM service wrapper
│   │   ├── stt.py       # Deepgram STT wrapper
│   │   └── tts.py       # Cartesia TTS wrapper
│   ├── db/
│   │   └── mongo.py     # Motor client + collections
│   ├── requirements.txt
│   └── .env
├── README.md
├── ADR.md
└── skills.md
```

---

## Core Workflows

### 1. Building the Pipecat Pipeline (`backend/pipeline.py`)

The pipeline is the heart of the voice bot. It chains services together:

```python
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService  # Groq is OpenAI-compatible
from pipecat.services.cartesia import CartesiaTTSService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
import os

async def create_pipeline(webrtc_connection):
    transport = SmallWebRTCTransport(
        webrtc_connection,
        params=SmallWebRTCParams(audio_in_enabled=True, audio_out_enabled=True),
    )

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    llm = OpenAILLMService(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id=os.getenv("CARTESIA_VOICE_ID"),
    )

    messages = [{"role": "system", "content": "You are Vaani, a helpful AI voice assistant. Be concise and friendly."}]
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline([
        transport.input(),
        stt,
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant(),
    ])

    task = PipelineTask(pipeline)
    return task, transport
```

**Key rules:**
- Always use `transport.input()` first and `transport.output()` last
- `context_aggregator.user()` goes before LLM, `context_aggregator.assistant()` goes after TTS
- Each session gets its own pipeline instance

---

### 2. WebRTC Signaling Endpoint (`backend/routes/webrtc.py`)

The browser sends a WebRTC SDP offer; the backend returns an SDP answer:

```python
from fastapi import APIRouter
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pydantic import BaseModel

router = APIRouter()

class OfferRequest(BaseModel):
    sdp: str
    type: str  # always "offer"

@router.post("/offer")
async def webrtc_offer(request: OfferRequest):
    connection = SmallWebRTCConnection()
    answer = await connection.handle_offer({"sdp": request.sdp, "type": request.type})

    # Start the pipeline in the background
    import asyncio
    from backend.pipeline import create_pipeline
    task, transport = await create_pipeline(connection)
    asyncio.create_task(run_pipeline(task, transport))

    return {"sdp": answer["sdp"], "type": answer["type"]}

async def run_pipeline(task, transport):
    runner = PipelineRunner()
    await runner.run(task)
```

**Key rules:**
- The `/offer` endpoint must be non-blocking — start pipeline as a background task
- Return the SDP answer immediately so the browser can complete WebRTC handshake
- One `SmallWebRTCConnection` per browser session

---

### 3. FastAPI App Entry Point (`backend/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.routes import webrtc, chat, health
from backend.db.mongo import connect_db, disconnect_db

load_dotenv()

app = FastAPI(title="Vaani Voice Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webrtc.router)
app.include_router(chat.router, prefix="/chat")
app.include_router(health.router)

@app.on_event("startup")
async def startup():
    await connect_db()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_db()
```

---

### 4. MongoDB Chat History (`backend/db/mongo.py`)

```python
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

client = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client["vaani"]

async def disconnect_db():
    if client:
        client.close()

async def save_message(session_id: str, role: str, content: str):
    await db["messages"].insert_one({
        "session_id": session_id,
        "role": role,           # "user" or "assistant"
        "content": content,
        "timestamp": datetime.utcnow(),
    })

async def get_messages(session_id: str) -> list:
    cursor = db["messages"].find(
        {"session_id": session_id},
        sort=[("timestamp", 1)]
    )
    return await cursor.to_list(length=100)
```

---

### 5. Environment Variables

All secrets live in `backend/.env`. Required keys:

```bash
GROQ_API_KEY=          # From console.groq.com (free)
DEEPGRAM_API_KEY=      # From deepgram.com (free)
CARTESIA_API_KEY=      # From cartesia.ai (free)
MONGODB_URI=           # From MongoDB Atlas (free M0)
GROQ_MODEL=llama-3.1-8b-instant
CARTESIA_VOICE_ID=a0e99841-438c-4a64-b679-ae501e7d6091
STUN_SERVER=stun:stun.l.google.com:19302
APP_HOST=0.0.0.0
APP_PORT=8000
```

Load with: `from dotenv import load_dotenv; load_dotenv()`

---

## Best Practices for This Project

### Pipeline
- ✅ Create a **new pipeline per session** — never share pipelines between users
- ✅ Always handle `on_client_disconnected` to clean up pipeline tasks
- ✅ Use `PipelineTask` with `allow_interruptions=True` for natural conversation
- ✅ Set a concise system prompt — shorter = faster LLM response = better voice UX

### WebRTC
- ✅ Use Google's free STUN: `stun:stun.l.google.com:19302`
- ✅ Run pipeline as `asyncio.create_task()` — never block the `/offer` endpoint
- ✅ For local dev: SmallWebRTC works without TURN server
- ⚠️ For production behind strict NAT: add a free TURN server (Metered.ca free tier)

### LLM (Groq)
- ✅ Use `llama-3.1-8b-instant` for lowest latency (best for voice)
- ✅ Keep system prompt under 200 words for voice bots
- ✅ Monitor free tier: 14,400 requests/day, 500K tokens/minute

### STT (Deepgram)
- ✅ Use `nova-2` model (best accuracy, included in free tier)
- ✅ Enable `endpointing` for natural turn detection

### TTS (Cartesia)
- ✅ Use streaming output — Pipecat handles this automatically
- ✅ Pick a voice ID from [cartesia.ai/voices](https://cartesia.ai/voices)

### MongoDB
- ✅ Always use `motor` (async) — never `pymongo` (sync) with FastAPI
- ✅ Index `session_id` field for fast message retrieval
- ✅ Free M0 tier: 512MB — archive old sessions periodically

---

## Running the Backend

```bash
cd vaani/backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: `http://localhost:8000/docs`

---

## Key References

- [Pipecat Docs](https://docs.pipecat.ai)
- [SmallWebRTC Transport](https://docs.pipecat.ai/server/services/transport/small-webrtc)
- [P2P WebRTC Example](https://github.com/pipecat-ai/pipecat-examples/tree/main/p2p-webrtc)
- [Groq API](https://console.groq.com/docs)
- [Deepgram STT](https://developers.deepgram.com)
- [Cartesia TTS](https://docs.cartesia.ai)
- [Motor Async MongoDB](https://motor.readthedocs.io)
