/**
 * useVoiceCall.js — WebRTC Voice Call Hook
 * Manages the entire voice call lifecycle using Pipecat JS SDK.
 */

import { useState, useRef, useCallback } from 'react'
import { sendOffer } from '../api'

export const CALL_STATE = {
    IDLE: 'idle',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    AI_SPEAKING: 'ai_speaking',
    USER_SPEAKING: 'user_speaking',
    DISCONNECTING: 'disconnecting',
    ERROR: 'error',
}

export function useVoiceCall({ sessionId, onTranscript }) {
    const [callState, setCallState] = useState(CALL_STATE.IDLE)
    const [error, setError] = useState(null)
    const [isMuted, setIsMuted] = useState(false)
    const clientRef = useRef(null)
    const pcRef = useRef(null)

    const startCall = useCallback(async () => {
        setError(null)
        setCallState(CALL_STATE.CONNECTING)

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })

            // Create WebRTC peer connection
            const pc = new RTCPeerConnection({
                iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
            })
            pcRef.current = pc

            // Add local audio track
            stream.getAudioTracks().forEach((track) => pc.addTrack(track, stream))

            // Play remote audio (AI voice)
            pc.ontrack = (event) => {
                const audio = document.getElementById('vaani-audio-output')
                if (audio && event.streams[0]) {
                    audio.srcObject = event.streams[0]
                    audio.play().catch(() => { })
                }
            }

            // Create SDP offer
            const offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            // Wait for ICE gathering to complete
            await new Promise((resolve) => {
                if (pc.iceGatheringState === 'complete') return resolve()
                pc.onicegatheringstatechange = () => {
                    if (pc.iceGatheringState === 'complete') resolve()
                }
                // Timeout fallback
                setTimeout(resolve, 3000)
            })

            // Send offer to backend
            const response = await sendOffer({
                sdp: pc.localDescription.sdp,
                type: pc.localDescription.type,
                session_id: sessionId,
            })

            // Set remote description (AI's answer)
            await pc.setRemoteDescription({
                sdp: response.data.sdp,
                type: response.data.type,
            })

            setCallState(CALL_STATE.CONNECTED)

            // Monitor connection state
            pc.onconnectionstatechange = () => {
                if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
                    setCallState(CALL_STATE.IDLE)
                }
            }
        } catch (err) {
            console.error('Call failed:', err)
            setError(err.message || 'Failed to start call')
            setCallState(CALL_STATE.ERROR)
            pcRef.current?.close()
            pcRef.current = null
        }
    }, [sessionId])

    const endCall = useCallback(() => {
        setCallState(CALL_STATE.DISCONNECTING)
        pcRef.current?.close()
        pcRef.current = null

        const audio = document.getElementById('vaani-audio-output')
        if (audio) {
            audio.srcObject = null
        }

        setTimeout(() => setCallState(CALL_STATE.IDLE), 500)
    }, [])

    const toggleMute = useCallback(() => {
        if (!pcRef.current) return
        pcRef.current.getSenders().forEach((sender) => {
            if (sender.track?.kind === 'audio') {
                sender.track.enabled = isMuted
            }
        })
        setIsMuted((prev) => !prev)
    }, [isMuted])

    return {
        callState,
        error,
        isMuted,
        startCall,
        endCall,
        toggleMute,
        isActive: callState === CALL_STATE.CONNECTED ||
            callState === CALL_STATE.AI_SPEAKING ||
            callState === CALL_STATE.USER_SPEAKING,
    }
}
