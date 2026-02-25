# Architecture Decision Records (ADR)

> ADRs document **why** we made specific technical choices for the Vaani project.
> Each record captures the context, decision, and consequences.

---

## ADR-001: Use Pipecat as the AI Voice Pipeline Framework

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need a framework to orchestrate the real-time pipeline of:
`audio input → STT → LLM → TTS → audio output`
Building this from scratch would require managing async streams, buffering, and service integrations manually.

### Decision
Use **[Pipecat](https://github.com/pipecat-ai/pipecat)** as the core pipeline framework.

### Reasons
- Purpose-built for real-time AI voice agents
- Handles the full pipeline: transport → STT → LLM → TTS → transport
- Supports SmallWebRTC transport natively
- Active open-source community, well-documented
- Works with Groq, Deepgram, Cartesia, and other free-tier services

### Consequences
- ✅ Rapid development — no need to build pipeline from scratch
- ✅ Built-in support for streaming audio chunks
- ⚠️ Tied to Pipecat's pipeline model (acceptable trade-off)

---

## ADR-002: Use SmallWebRTC as the Transport Layer

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need a real-time, low-latency audio transport between the browser and the backend. Options considered:
1. **Daily.co** — managed WebRTC, but requires paid account for production
2. **SmallWebRTC** — lightweight, serverless P2P WebRTC built into Pipecat
3. **WebSockets** — simpler but higher latency, not ideal for voice

### Decision
Use **SmallWebRTC** (Pipecat's built-in lightweight WebRTC transport).

### Reasons
- **Zero cost** — no third-party WebRTC server needed
- Direct peer-to-peer connection between browser and backend
- Natively supported by Pipecat (`pipecat-ai[webrtc]`)
- Uses standard WebRTC APIs — works in all modern browsers
- STUN server (Google's free public STUN) handles NAT traversal for most cases

### Consequences
- ✅ No infrastructure cost
- ✅ Low latency P2P audio streaming
- ⚠️ For production behind strict NAT/firewalls, a TURN server may be needed (can use free tier of Metered.ca or Twilio STUN/TURN free tier)

---

## ADR-003: Use Groq as the LLM Provider

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need an LLM for generating AI responses. Options:
1. **OpenAI GPT-4** — paid, expensive
2. **Google Gemini API** — has free tier but rate limits
3. **Groq** — free tier with very fast inference (LPU hardware)

### Decision
Use **Groq** with **Llama 3.1 8B** or **Mixtral 8x7B** model.

### Reasons
- **Free tier**: 14,400 requests/day, 500,000 tokens/minute
- Ultra-fast inference (LPU chips) — critical for low-latency voice
- Supports OpenAI-compatible API — easy to integrate with Pipecat
- Llama 3 / Mixtral are high-quality open models

### Consequences
- ✅ Zero cost for development and moderate usage
- ✅ Very fast response times (important for voice UX)
- ⚠️ Rate limits apply on free tier (14,400 req/day)

---

## ADR-004: Use Deepgram for Speech-to-Text (STT)

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need real-time speech-to-text. Options:
1. **OpenAI Whisper (local)** — free but requires GPU for real-time
2. **Deepgram** — free tier (45,000 min/year), streaming STT
3. **Google Speech-to-Text** — paid after free tier

### Decision
Use **Deepgram** (free tier) as the primary STT.
Fallback: **faster-whisper** (local CPU) for development.

### Reasons
- Deepgram free tier: 45,000 minutes/year (~125 min/day) — enough for development
- Pipecat has native `DeepgramSTTService` integration
- Streaming transcription — low latency word-by-word output
- Excellent accuracy for English

### Consequences
- ✅ Zero cost within free tier limits
- ✅ Real-time streaming transcription
- ⚠️ 45,000 min/year limit — monitor usage in production

---

## ADR-005: Use Cartesia for Text-to-Speech (TTS)

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need natural-sounding TTS. Options:
1. **Google TTS (gTTS)** — free but robotic voice, no streaming
2. **Cartesia** — free tier, high-quality streaming TTS
3. **ElevenLabs** — excellent quality but paid

### Decision
Use **Cartesia** (free tier) as the primary TTS.
Fallback: **gTTS** or **pyttsx3** for local development.

### Reasons
- Cartesia free tier available for development
- Pipecat has native `CartesiaTTSService` integration
- Streaming audio output — chunks sent as they're generated
- Natural-sounding voices

### Consequences
- ✅ High-quality voice output
- ✅ Streaming TTS (low perceived latency)
- ⚠️ Check Cartesia free tier limits before production

---

## ADR-006: Use MongoDB Atlas as the Database

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need to store chat history and session data. Options:
1. **PostgreSQL** — relational, requires hosting
2. **MongoDB Atlas** — free M0 tier (512MB), flexible schema
3. **SQLite** — local only, not suitable for production

### Decision
Use **MongoDB Atlas** (Free M0 cluster).

### Reasons
- **Free M0 tier**: 512MB storage, shared cluster — sufficient for MVP
- Flexible document model — perfect for chat messages (variable structure)
- `motor` async driver works well with FastAPI
- No server to manage — fully managed cloud service

### Consequences
- ✅ Zero cost for MVP
- ✅ Flexible schema for chat messages
- ⚠️ 512MB limit on free tier — archive old sessions if needed

---

## ADR-007: Use FastAPI as the Backend Web Framework

**Date:** 2026-02-18
**Status:** Accepted

### Context
We need a Python web framework to:
- Handle WebRTC signaling (POST /offer)
- Serve chat history API
- Run Pipecat pipelines asynchronously

### Decision
Use **FastAPI** with **Uvicorn** ASGI server.

### Reasons
- Async-first — compatible with Pipecat's async pipeline model
- Fast and lightweight
- Auto-generates API docs (Swagger UI)
- WebSocket support built-in
- Works well with `motor` (async MongoDB driver)

### Consequences
- ✅ Full async support for concurrent voice sessions
- ✅ Easy to add REST endpoints for chat
- ✅ Built-in request validation with Pydantic

---

## ADR-008: Use Pipecat JS Client SDK for Browser

**Date:** 2026-02-18
**Status:** Accepted

### Context
The browser client needs to:
- Capture microphone audio
- Establish WebRTC connection with the backend
- Send/receive RTVI protocol messages

### Decision
Use **`@pipecat-ai/client-js`** (Pipecat JavaScript Client SDK).

### Reasons
- Official SDK — handles RTVI protocol automatically
- Manages WebRTC connection lifecycle
- Works with SmallWebRTC transport on the server side
- Handles SDP offer/answer exchange

### Consequences
- ✅ Consistent protocol between client and server
- ✅ Reduces boilerplate WebRTC code in the browser
- ✅ React SDK available when frontend is built

---

## Summary Table

| Decision | Choice | Cost |
|----------|--------|------|
| Pipeline Framework | Pipecat | Free (OSS) |
| Transport | SmallWebRTC | Free |
| LLM | Groq (Llama 3) | Free tier |
| STT | Deepgram | Free tier |
| TTS | Cartesia | Free tier |
| Database | MongoDB Atlas M0 | Free tier |
| Backend | FastAPI + Uvicorn | Free (OSS) |
| Client SDK | Pipecat JS SDK | Free (OSS) |
| STUN Server | Google STUN | Free |

> 💰 **Total Monthly Cost: $0** (within free tier limits)
