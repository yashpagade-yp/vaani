/**
 * api.js — Backend API Client
 * All calls to the FastAPI backend go through here.
 * Uses Vite's proxy so /api → http://localhost:8000
 */

import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    timeout: 10000,
    headers: { 'Content-Type': 'application/json' },
})

// ── Health ────────────────────────────────────────────────────
export const checkHealth = () => api.get('/health')

// ── Chat ─────────────────────────────────────────────────────
export const getChatHistory = (sessionId) =>
    api.get(`/chat/${sessionId}`)

export const sendChatMessage = (sessionId, content) =>
    api.post(`/chat/${sessionId}`, { content, role: 'user' })

export const clearChatHistory = (sessionId) =>
    api.delete(`/chat/${sessionId}`)

// ── WebRTC ────────────────────────────────────────────────────
export const sendOffer = (offerData) =>
    api.post('/offer', offerData)

export default api
