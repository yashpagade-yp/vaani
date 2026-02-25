/**
 * VoiceOrb.jsx — The glowing animated mic button
 * The centerpiece of the voice call UI.
 */

import { useEffect, useRef } from 'react'
import { CALL_STATE } from '../hooks/useVoiceCall'
import styles from './VoiceOrb.module.css'

const STATE_LABELS = {
    [CALL_STATE.IDLE]: 'Tap to speak',
    [CALL_STATE.CONNECTING]: 'Connecting...',
    [CALL_STATE.CONNECTED]: 'Listening...',
    [CALL_STATE.AI_SPEAKING]: 'Vaani is speaking',
    [CALL_STATE.USER_SPEAKING]: 'I hear you...',
    [CALL_STATE.DISCONNECTING]: 'Ending call...',
    [CALL_STATE.ERROR]: 'Connection failed',
}

export default function VoiceOrb({ callState, isMuted, onStart, onEnd, onToggleMute, error }) {
    const isActive = callState === CALL_STATE.CONNECTED ||
        callState === CALL_STATE.AI_SPEAKING ||
        callState === CALL_STATE.USER_SPEAKING
    const isConnecting = callState === CALL_STATE.CONNECTING ||
        callState === CALL_STATE.DISCONNECTING
    const isError = callState === CALL_STATE.ERROR

    const handleOrbClick = () => {
        if (isConnecting) return
        if (isActive) onEnd()
        else onStart()
    }

    return (
        <div className={styles.container}>
            {/* Ambient background glow */}
            <div className={`${styles.ambientGlow} ${isActive ? styles.ambientActive : ''}`} />

            {/* Pulse rings (only when active) */}
            {isActive && (
                <>
                    <div className={`${styles.ring} ${styles.ring1}`} />
                    <div className={`${styles.ring} ${styles.ring2}`} />
                    <div className={`${styles.ring} ${styles.ring3}`} />
                </>
            )}

            {/* Main orb button */}
            <button
                className={`${styles.orb} ${isActive ? styles.orbActive : ''} ${isError ? styles.orbError : ''} ${isConnecting ? styles.orbConnecting : ''}`}
                onClick={handleOrbClick}
                disabled={isConnecting}
                aria-label={isActive ? 'End voice call' : 'Start voice call'}
                id="voice-orb-btn"
            >
                {/* Waveform bars (shown when active) */}
                {isActive && !isMuted ? (
                    <div className={styles.waveform} aria-hidden="true">
                        {[...Array(5)].map((_, i) => (
                            <div
                                key={i}
                                className={styles.bar}
                                style={{ animationDelay: `${i * 0.12}s` }}
                            />
                        ))}
                    </div>
                ) : isConnecting ? (
                    <div className={styles.spinner} aria-hidden="true" />
                ) : (
                    <MicIcon muted={isMuted && isActive} />
                )}
            </button>

            {/* Status label */}
            <p className={`${styles.label} ${isError ? styles.labelError : ''}`}>
                {isError ? (error || STATE_LABELS[callState]) : STATE_LABELS[callState]}
            </p>

            {/* Mute button (only when in call) */}
            {isActive && (
                <button
                    className={`${styles.muteBtn} ${isMuted ? styles.muteBtnActive : ''}`}
                    onClick={onToggleMute}
                    aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                    id="mute-btn"
                >
                    {isMuted ? <MicOffIcon /> : <MicIcon small />}
                    <span>{isMuted ? 'Unmute' : 'Mute'}</span>
                </button>
            )}

            {/* Hidden audio element for AI voice output */}
            <audio id="vaani-audio-output" autoPlay playsInline style={{ display: 'none' }} />
        </div>
    )
}

function MicIcon({ muted, small }) {
    const size = small ? 18 : 28
    return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="2" width="6" height="11" rx="3" />
            <path d="M5 10a7 7 0 0 0 14 0" />
            <line x1="12" y1="19" x2="12" y2="22" />
            <line x1="8" y1="22" x2="16" y2="22" />
            {muted && <line x1="3" y1="3" x2="21" y2="21" stroke="var(--accent-red)" />}
        </svg>
    )
}

function MicOffIcon() {
    return (
        <svg width={18} height={18} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="1" y1="1" x2="23" y2="23" />
            <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6" />
            <path d="M17 16.95A7 7 0 0 1 5 10v-1m14 0v1a7 7 0 0 1-.11 1.23" />
            <line x1="12" y1="19" x2="12" y2="22" />
            <line x1="8" y1="22" x2="16" y2="22" />
        </svg>
    )
}
