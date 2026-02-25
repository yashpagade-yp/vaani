# Vaani Frontend

> Dark/minimal React + Vite web app for the Vaani AI voice assistant.  
> Supports real-time **voice calls** (WebRTC) and **text chat** — both connected to the Vaani FastAPI backend.

---

## Quick Start

> **Prerequisite:** Node.js must be installed. Backend must be running on port 8000.

### 1. Install dependencies
```powershell
cd vaani/frontend
npm install
```

### 2. Start the dev server
```powershell
node -e "require('child_process').execSync('npm run dev', {stdio:'inherit', cwd:process.cwd()})"
```

### 3. Open in browser
```
http://localhost:3000
```

---

## Project Structure

```
frontend/
├── index.html                    # Entry HTML (fonts, meta tags)
├── vite.config.js                # Vite config + proxy to backend
├── package.json
│
└── src/
    ├── main.jsx                  # React entry point
    ├── App.jsx                   # Root component (tabs, layout)
    ├── App.module.css            # App-level styles
    ├── index.css                 # Global design system (tokens, animations)
    ├── api.js                    # All backend API calls (axios)
    │
    ├── components/
    │   ├── Header.jsx            # Sticky top bar with logo + backend status
    │   ├── Header.module.css
    │   ├── VoiceOrb.jsx          # Glowing mic button with pulse rings
    │   ├── VoiceOrb.module.css
    │   ├── ChatPanel.jsx         # Full text chat interface
    │   └── ChatPanel.module.css
    │
    └── hooks/
        ├── useVoiceCall.js       # WebRTC call lifecycle hook
        └── useChat.js            # Chat state + API hook
```

---

## Features

### 🎙️ Voice Call Tab
- **Glowing orb** — tap to start/end a voice call
- **Pulse rings** — animated rings expand outward during a call
- **Waveform bars** — animated bars show when audio is flowing
- **Mute button** — mute/unmute your mic mid-call
- **State labels** — Idle → Connecting → Listening → AI Speaking

### 💬 Text Chat Tab
- **Message bubbles** — user (purple) and Vaani (dark) bubbles
- **Optimistic UI** — messages appear instantly before server confirms
- **Typing indicator** — animated dots while AI is responding
- **Auto-scroll** — always scrolls to the latest message
- **Clear history** — delete all messages for the session
- **Keyboard shortcut** — `Enter` to send, `Shift+Enter` for newline

### 🟢 Backend Status
- Live health check every 30 seconds
- Green dot in header = backend online
- Offline banner on Voice tab if backend is down

---

## How Voice Calls Work

```
User clicks orb
    ↓
Browser requests microphone permission
    ↓
Creates RTCPeerConnection + SDP offer
    ↓
POST /api/offer → FastAPI backend
    ↓
Backend returns SDP answer (Pipecat pipeline starts)
    ↓
WebRTC handshake completes
    ↓
Audio: mic → backend → Deepgram STT → Groq LLM → Cartesia TTS → speaker
```

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/health` | Backend status check |
| `POST` | `/api/offer` | Start a voice call (WebRTC SDP) |
| `GET` | `/api/chat/{session_id}` | Load chat history |
| `POST` | `/api/chat/{session_id}` | Send a text message |
| `DELETE` | `/api/chat/{session_id}` | Clear chat history |

> All `/api/*` calls are proxied to `http://localhost:8000` by Vite in development.

---

## Design System

The app uses a custom CSS design system defined in `src/index.css`.

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#080810` | Page background |
| `--bg-card` | `#13131f` | Card/panel backgrounds |
| `--purple-core` | `#7c3aed` | Primary accent |
| `--purple-bright` | `#a855f7` | Highlights, active states |
| `--text-primary` | `#f1f0ff` | Main text |
| `--text-secondary` | `#a09ec0` | Subtitles, labels |

**Animations:** `pulse-ring`, `wave-bar`, `orb-breathe`, `fade-in-up`, `spin`

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server on port 3000 |
| `npm run build` | Build for production → `dist/` |
| `npm run preview` | Preview the production build |

---

## Environment / Configuration

No `.env` file needed for the frontend. The backend URL is configured in `vite.config.js`:

```js
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // ← Change this if backend runs elsewhere
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
}
```

---

## Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| React | 19 | UI framework |
| Vite | 7 | Build tool + dev server |
| `@pipecat-ai/client-js` | latest | Pipecat JS SDK |
| `@pipecat-ai/client-react` | latest | React hooks for Pipecat |
| axios | latest | HTTP client for API calls |

---

## Running Both Backend + Frontend

**Terminal 1 — Backend:**
```powershell
cd vaani/backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd vaani/frontend
node -e "require('child_process').execSync('npm run dev', {stdio:'inherit', cwd:process.cwd()})"
```

Then open **http://localhost:3000** 🎉
