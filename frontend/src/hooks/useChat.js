/**
 * useChat.js — Chat History Hook
 * Manages text chat state and API calls to the backend.
 */

import { useState, useCallback, useRef } from 'react'
import { getChatHistory, sendChatMessage, clearChatHistory } from '../api'

export function useChat(sessionId) {
    const [messages, setMessages] = useState([])
    const [isLoading, setIsLoading] = useState(false)
    const [isSending, setIsSending] = useState(false)
    const [error, setError] = useState(null)

    const loadHistory = useCallback(async () => {
        setIsLoading(true)
        setError(null)
        try {
            const res = await getChatHistory(sessionId)
            setMessages(res.data.messages || [])
        } catch (err) {
            // Empty history is fine
            setMessages([])
        } finally {
            setIsLoading(false)
        }
    }, [sessionId])

    const sendMessage = useCallback(async (content) => {
        if (!content.trim() || isSending) return

        const optimisticMsg = {
            id: `temp-${Date.now()}`,
            role: 'user',
            content: content.trim(),
            timestamp: new Date().toISOString(),
            isOptimistic: true,
        }

        // Optimistically add user message
        setMessages((prev) => [...prev, optimisticMsg])
        setIsSending(true)
        setError(null)

        try {
            const res = await sendChatMessage(sessionId, content.trim())
            const aiReply = res.data  // backend now returns the AI reply

            // Confirm the optimistic user message (remove optimistic flag)
            // and append the AI reply as a new message
            setMessages((prev) => [
                ...prev.map((m) =>
                    m.id === optimisticMsg.id
                        ? { ...optimisticMsg, isOptimistic: false }
                        : m
                ),
                { ...aiReply, isOptimistic: false },
            ])
        } catch (err) {
            setError('Failed to send message. Please try again.')
            // Remove optimistic message on failure
            setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id))
        } finally {
            setIsSending(false)
        }
    }, [sessionId, isSending])

    const clearHistory = useCallback(async () => {
        try {
            await clearChatHistory(sessionId)
            setMessages([])
        } catch (err) {
            setError('Failed to clear history.')
        }
    }, [sessionId])

    return {
        messages,
        isLoading,
        isSending,
        error,
        loadHistory,
        sendMessage,
        clearHistory,
        setMessages,
    }
}
