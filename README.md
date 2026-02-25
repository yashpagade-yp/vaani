# 🎙️ Vaani — AI-Powered Voice + Chat Web App

> **Vaani** (Hindi: वाणी, meaning *voice/speech*) is a zero-cost, real-time AI voice and chat web application built with [Pipecat](https://docs.pipecat.ai), SmallWebRTC, Groq (LLM), Google Gemini (STT/TTS), and MongoDB.

---

## 🌟 What Is Vaani?

Vaani lets users **talk to an AI agent** directly from their browser — like a phone call, but with an AI. It also supports **text chat** in the same session. Think of it like [eigi.ai](https://eigi.ai) — a voice + chat AI agent on the web.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER (Web Client)                         │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│   │  Pipecat JS  │    │  WebRTC API  │    │   Chat UI (Text)    │  │
│   │  Client SDK  │    │  (mic/audio) │    │   REST / WebSocket  │  │
│   └──────┬───────┘    └──────┬───────┘    └──────────┬──────────┘  │
│          │                   │                        │             │
└──────────┼───────────────────┼────────────────────────┼────────────┘
           │  RTVI Protocol    │  WebRTC (audio/video)  │  HTTP/WS
           │  (signaling)      │  P2P Media Stream      │
           ▼                   ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Pipecat)                     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Server                            │   │
│  │   POST /offer  ──► SmallWebRTC Signaling (SDP exchange)     │   │
│  │   GET  /chat   ──► Chat History (MongoDB)                   │   │
│  │   WS   /ws     ──► Real-time text chat                      │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │               Pipecat Pipeline (per session)                 │   │
│  │                                                              │   │
│  │  SmallWebRTC  ──► STT (Deepgram/Whisper) ──► LLM (Groq)    │   │
│  │  Transport         Speech-to-Text            Llama-3/Mixtral │   │
│  │                                                    │         │   │
│  │  SmallWebRTC  ◄── TTS (Cartesia/gTTS)  ◄──────────┘        │   │
│  │  Transport         Text-to-Speech                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    MongoDB Atlas (Free Tier)                  │   │
│  │   - Chat history per session                                 │   │
│  │   - User sessions & metadata                                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 🔄 Call Flow (Step-by-Step)

```
User opens browser
      │
      ▼
1. Browser loads web page
      │
      ▼
2. User clicks "Start Call"
      │
      ▼
3. Browser captures mic → creates WebRTC offer (SDP)
      │
      ▼
4. POST /offer → FastAPI backend (signaling)
      │
      ▼
5. Backend creates Pipecat pipeline + SmallWebRTC transport
   Returns SDP answer to browser
      │
      ▼
6. P2P WebRTC connection established (audio stream flows)
      │
      ▼
7. User speaks → audio → STT (speech-to-text)
      │
      ▼
8. Text → Groq LLM (Llama 3 / Mixtral) → AI response text
      │
      ▼
9. Response text → TTS (text-to-speech) → audio chunks
      │
      ▼
10. Audio streams back to browser via WebRTC → user hears AI
      │
      ▼
11. Chat messages saved to MongoDB
```

---

## 🛠️ Tech Stack (100% Free / Open Source)

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | [Pipecat](https://github.com/pipecat-ai/pipecat) | AI voice pipeline orchestration |
| **Transport** | SmallWebRTC | Serverless P2P WebRTC, no paid infra needed |
| **Backend API** | FastAPI (Python) | Fast async web server |
| **LLM** | [Groq](https://groq.com) (Llama 3 / Mixtral) | Free tier, ultra-fast inference |
| **STT** | Deepgram (free tier) or `faster-whisper` (local) | Speech-to-text |
| **TTS** | Cartesia (free tier) or `gTTS` / `pyttsx3` (local) | Text-to-speech |
| **Database** | MongoDB Atlas (Free M0 tier) | Chat history & sessions |
| **Client SDK** | Pipecat JS SDK (`@pipecat-ai/client-js`) | Browser WebRTC + RTVI |

> 💡 **Zero Cost Strategy**: Groq free tier (14,400 req/day), MongoDB Atlas M0 (512MB free), Deepgram free tier (45,000 min/year). All free!

---

## 📁 Project Structure

```
vaani/
├── backend/                    # Python FastAPI + Pipecat server
│   ├── main.py                 # FastAPI app entry point
│   ├── pipeline.py             # Pipecat pipeline definition
│   ├── routes/
│   │   ├── webrtc.py           # POST /offer — WebRTC signaling
│   │   ├── chat.py             # GET/POST /chat — chat history
│   │   └── health.py           # GET /health
│   ├── services/
│   │   ├── llm.py              # Groq LLM service
│   │   ├── stt.py              # STT service (Deepgram/Whisper)
│   │   └── tts.py              # TTS service (Cartesia/gTTS)
│   ├── db/
│   │   └── mongo.py            # MongoDB connection & models
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment variables (secrets)
├── README.md                   # This file
└── ADR.md                      # Architecture Decision Records
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- MongoDB Atlas account (free)
- Groq API key (free) → [console.groq.com](https://console.groq.com)
- Deepgram API key (free) → [deepgram.com](https://deepgram.com) *(or use local Whisper)*

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd vaani/backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and fill in your keys:

```bash
cp .env.example .env
```

### 3. Run the Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔑 Environment Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `GROQ_API_KEY` | Groq LLM API key | [console.groq.com](https://console.groq.com) |
| `DEEPGRAM_API_KEY` | Speech-to-text | [deepgram.com](https://deepgram.com) |
| `CARTESIA_API_KEY` | Text-to-speech | [cartesia.ai](https://cartesia.ai) |
| `MONGODB_URI` | MongoDB Atlas connection string | [mongodb.com/atlas](https://mongodb.com/atlas) |
| `STUN_SERVER` | STUN server for WebRTC NAT | `stun:stun.l.google.com:19302` (free) |

---

## 📚 Key References

- [Pipecat Docs](https://docs.pipecat.ai)
- [SmallWebRTC Transport](https://docs.pipecat.ai/server/services/transport/small-webrtc)
- [Pipecat Client SDK](https://docs.pipecat.ai/client/introduction)
- [Pipecat Examples (P2P WebRTC)](https://github.com/pipecat-ai/pipecat-examples/tree/main/p2p-webrtc)
- [Groq Free Tier](https://console.groq.com)

---

## 📝 License

MIT License — free to use, modify, and distribute.
