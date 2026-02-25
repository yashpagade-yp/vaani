/**
 * ChatPanel.jsx — Text chat interface
 * Connects to the backend /chat/{session_id} endpoints.
 */

import { useEffect, useRef, useState } from 'react'
import styles from './ChatPanel.module.css'

export default function ChatPanel({ messages, isLoading, isSending, error, onSend, onClear }) {
    const [input, setInput] = useState('')
    const bottomRef = useRef(null)
    const inputRef = useRef(null)

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!input.trim() || isSending) return
        onSend(input)
        setInput('')
        inputRef.current?.focus()
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e)
        }
    }

    return (
        <div className={styles.panel}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <div className={styles.headerDot} />
                    <span className={styles.headerTitle}>Chat</span>
                    {messages.length > 0 && (
                        <span className={styles.msgCount}>{messages.length}</span>
                    )}
                </div>
                {messages.length > 0 && (
                    <button
                        className={styles.clearBtn}
                        onClick={onClear}
                        aria-label="Clear chat history"
                        id="clear-chat-btn"
                    >
                        Clear
                    </button>
                )}
            </div>

            {/* Messages area */}
            <div className={styles.messages} role="log" aria-live="polite" aria-label="Chat messages">
                {isLoading ? (
                    <div className={styles.loadingState}>
                        <div className={styles.loadingDots}>
                            <span /><span /><span />
                        </div>
                        <p>Loading history...</p>
                    </div>
                ) : messages.length === 0 ? (
                    <div className={styles.emptyState}>
                        <div className={styles.emptyIcon}>
                            <ChatBubbleIcon />
                        </div>
                        <p className={styles.emptyTitle}>No messages yet</p>
                        <p className={styles.emptySubtitle}>
                            Type a message below or start a voice call to chat with Vaani
                        </p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <MessageBubble
                            key={msg.id || idx}
                            message={msg}
                            isOptimistic={msg.isOptimistic}
                        />
                    ))
                )}

                {/* Typing indicator when AI is responding */}
                {isSending && (
                    <div className={`${styles.bubble} ${styles.bubbleAssistant}`}>
                        <div className={styles.typingIndicator}>
                            <span /><span /><span />
                        </div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Error banner */}
            {error && (
                <div className={styles.errorBanner} role="alert">
                    <span>{error}</span>
                </div>
            )}

            {/* Input area */}
            <form className={styles.inputArea} onSubmit={handleSubmit}>
                <textarea
                    ref={inputRef}
                    className={styles.input}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message Vaani... (Enter to send)"
                    rows={1}
                    maxLength={2000}
                    disabled={isSending}
                    aria-label="Chat message input"
                    id="chat-input"
                />
                <button
                    type="submit"
                    className={styles.sendBtn}
                    disabled={!input.trim() || isSending}
                    aria-label="Send message"
                    id="send-btn"
                >
                    <SendIcon />
                </button>
            </form>
        </div>
    )
}

function MessageBubble({ message, isOptimistic }) {
    const isUser = message.role === 'user'
    // Append 'Z' if missing so JS parses as UTC → auto-converts to local timezone (IST)
    const rawTs = message.timestamp
    const ts = rawTs && !rawTs.endsWith('Z') && !rawTs.includes('+') ? rawTs + 'Z' : rawTs
    const time = ts
        ? new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : ''

    return (
        <div
            className={`${styles.messageRow} ${isUser ? styles.messageRowUser : styles.messageRowAssistant}`}
            style={{ animation: 'fade-in-up 0.2s ease-out' }}
        >
            {!isUser && (
                <div className={styles.avatar} aria-hidden="true">V</div>
            )}
            <div className={`${styles.bubble} ${isUser ? styles.bubbleUser : styles.bubbleAssistant} ${isOptimistic ? styles.bubbleOptimistic : ''}`}>
                <p className={styles.bubbleText}>{message.content}</p>
                {time && <span className={styles.bubbleTime}>{time}</span>}
            </div>
        </div>
    )
}

function SendIcon() {
    return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
    )
}

function ChatBubbleIcon() {
    return (
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
    )
}
