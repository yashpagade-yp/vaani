/**
 * App.jsx — Main Application
 * Ties together the voice call and chat interfaces.
 */

import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import VoiceOrb from './components/VoiceOrb'
import ChatPanel from './components/ChatPanel'
import { useVoiceCall } from './hooks/useVoiceCall'
import { useChat } from './hooks/useChat'
import { checkHealth } from './api'
import styles from './App.module.css'

// Generate a stable session ID for this browser tab
const SESSION_ID = `sess-${Math.random().toString(36).slice(2, 10)}`

export default function App() {
  const [backendOnline, setBackendOnline] = useState(false)
  const [activeTab, setActiveTab] = useState('voice') // 'voice' | 'chat'

  // Voice call hook
  const {
    callState,
    error: callError,
    isMuted,
    startCall,
    endCall,
    toggleMute,
    isActive,
  } = useVoiceCall({ sessionId: SESSION_ID })

  // Chat hook
  const {
    messages,
    isLoading: chatLoading,
    isSending,
    error: chatError,
    loadHistory,
    sendMessage,
    clearHistory,
  } = useChat(SESSION_ID)

  // Check backend health on mount and every 30s
  useEffect(() => {
    const ping = async () => {
      try {
        await checkHealth()
        setBackendOnline(true)
      } catch {
        setBackendOnline(false)
      }
    }
    ping()
    const interval = setInterval(ping, 30000)
    return () => clearInterval(interval)
  }, [])

  // Load chat history when switching to chat tab
  useEffect(() => {
    if (activeTab === 'chat') {
      loadHistory()
    }
  }, [activeTab, loadHistory])

  return (
    <div className={styles.app}>
      <Header isConnected={backendOnline} />

      <main className={styles.main}>
        {/* Hero section */}
        <div className={styles.hero}>
          <h1 className={styles.heroTitle}>
            Talk to <span className={styles.heroAccent}>Vaani</span>
          </h1>
          <p className={styles.heroSubtitle}>
            Your AI voice assistant — speak naturally or type your thoughts
          </p>
        </div>

        {/* Tab switcher */}
        <div className={styles.tabs} role="tablist" aria-label="Interaction mode">
          <button
            role="tab"
            aria-selected={activeTab === 'voice'}
            className={`${styles.tab} ${activeTab === 'voice' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('voice')}
            id="tab-voice"
          >
            <MicTabIcon />
            Voice Call
            {isActive && <span className={styles.tabBadge} aria-label="Call active" />}
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'chat'}
            className={`${styles.tab} ${activeTab === 'chat' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('chat')}
            id="tab-chat"
          >
            <ChatTabIcon />
            Text Chat
            {messages.length > 0 && (
              <span className={styles.tabCount}>{messages.length}</span>
            )}
          </button>
        </div>

        {/* Content panels */}
        <div className={styles.content}>
          {/* Voice panel */}
          <div
            role="tabpanel"
            aria-labelledby="tab-voice"
            className={`${styles.panel} ${activeTab === 'voice' ? styles.panelVisible : styles.panelHidden}`}
          >
            <div className={styles.voicePanel}>
              {!backendOnline && (
                <div className={styles.offlineBanner} role="alert">
                  <span>Backend offline — start the server first</span>
                  <code>.\venv\Scripts\python.exe -m uvicorn main:app --port 8000</code>
                </div>
              )}
              <VoiceOrb
                callState={callState}
                isMuted={isMuted}
                onStart={startCall}
                onEnd={endCall}
                onToggleMute={toggleMute}
                error={callError}
              />
              <div className={styles.voiceHints}>
                <HintCard icon="🎙️" text="Tap the orb to start a voice call" />
                <HintCard icon="🤖" text="Vaani listens and responds in real-time" />
                <HintCard icon="🔇" text="Mute yourself anytime during the call" />
              </div>
            </div>
          </div>

          {/* Chat panel */}
          <div
            role="tabpanel"
            aria-labelledby="tab-chat"
            className={`${styles.panel} ${activeTab === 'chat' ? styles.panelVisible : styles.panelHidden}`}
          >
            <div className={styles.chatWrapper}>
              <ChatPanel
                messages={messages}
                isLoading={chatLoading}
                isSending={isSending}
                error={chatError}
                onSend={sendMessage}
                onClear={clearHistory}
              />
            </div>
          </div>
        </div>

        {/* Session info footer */}
        <div className={styles.sessionInfo}>
          <span className={styles.sessionLabel}>Session</span>
          <code className={styles.sessionId}>{SESSION_ID}</code>
        </div>
      </main>
    </div>
  )
}

function HintCard({ icon, text }) {
  return (
    <div className={styles.hintCard}>
      <span className={styles.hintIcon} aria-hidden="true">{icon}</span>
      <span className={styles.hintText}>{text}</span>
    </div>
  )
}

function MicTabIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="2" width="6" height="11" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
    </svg>
  )
}

function ChatTabIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}
