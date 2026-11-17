import { useCallback, useEffect, useRef, useState } from 'react'
import { ChatApiError, resetSession, streamChat, type Source } from './api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: number
  sources?: Source[]
  error?: { message: string; retryable: boolean }
  streaming?: boolean
}

const STORE_KEY = 'mm-chat'
export const MAX_INPUT_CHARS = 1000

interface Stored {
  sessionId: string | null
  messages: ChatMessage[]
}

function load(): Stored {
  try {
    const raw = sessionStorage.getItem(STORE_KEY)
    if (raw) {
      const s = JSON.parse(raw) as Stored
      return { sessionId: s.sessionId, messages: s.messages.filter((m) => !m.streaming) }
    }
  } catch {
    /* ignore corrupt storage */
  }
  return { sessionId: null, messages: [] }
}

const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36)

export function useChat(baseUrl: string) {
  const [messages, setMessages] = useState<ChatMessage[]>(() => load().messages)
  const [sessionId, setSessionId] = useState<string | null>(() => load().sessionId)
  const [busy, setBusy] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  // Persist only for this browser tab (sessionStorage) — nothing long-lived.
  useEffect(() => {
    try {
      sessionStorage.setItem(STORE_KEY, JSON.stringify({ sessionId, messages }))
    } catch {
      /* storage unavailable */
    }
  }, [sessionId, messages])

  useEffect(() => () => abortRef.current?.abort(), [])

  const patch = (id: string, fn: (m: ChatMessage) => ChatMessage) =>
    setMessages((ms) => ms.map((m) => (m.id === id ? fn(m) : m)))

  const run = useCallback(
    async (text: string, assistantId: string) => {
      const ctrl = new AbortController()
      abortRef.current = ctrl
      setBusy(true)
      try {
        for await (const evt of streamChat(baseUrl, { message: text, session_id: sessionId }, ctrl.signal)) {
          if (evt.type === 'meta') setSessionId(evt.sessionId)
          else if (evt.type === 'delta') patch(assistantId, (m) => ({ ...m, content: m.content + evt.text }))
          else if (evt.type === 'sources') patch(assistantId, (m) => ({ ...m, sources: evt.sources }))
          else if (evt.type === 'error')
            patch(assistantId, (m) => ({ ...m, error: { message: evt.message, retryable: evt.retryable } }))
        }
      } catch (e) {
        if ((e as Error).name === 'AbortError') return
        const err = e instanceof ChatApiError ? e : new ChatApiError('Something went wrong. Please try again.', true)
        patch(assistantId, (m) => ({ ...m, error: { message: err.message, retryable: err.retryable } }))
      } finally {
        patch(assistantId, (m) => ({ ...m, streaming: false }))
        setBusy(false)
        abortRef.current = null
      }
    },
    [baseUrl, sessionId],
  )

  const send = useCallback(
    (raw: string) => {
      const text = raw.trim().slice(0, MAX_INPUT_CHARS)
      if (!text || busy) return
      const now = Date.now()
      const assistantId = uid()
      setMessages((ms) => [
        ...ms,
        { id: uid(), role: 'user', content: text, createdAt: now },
        { id: assistantId, role: 'assistant', content: '', createdAt: now, streaming: true },
      ])
      void run(text, assistantId)
    },
    [busy, run],
  )

  /** Re-run the user message that preceded a failed assistant answer. */
  const retry = useCallback(
    (assistantId: string) => {
      if (busy) return
      const idx = messages.findIndex((m) => m.id === assistantId)
      const prevUser = [...messages.slice(0, idx)].reverse().find((m) => m.role === 'user')
      if (!prevUser) return
      patch(assistantId, (m) => ({ ...m, content: '', error: undefined, sources: undefined, streaming: true, createdAt: Date.now() }))
      void run(prevUser.content, assistantId)
    },
    [busy, messages, run],
  )

  const stop = useCallback(() => abortRef.current?.abort(), [])

  const clear = useCallback(() => {
    abortRef.current?.abort()
    if (sessionId) void resetSession(baseUrl, sessionId)
    setSessionId(null)
    setMessages([])
  }, [baseUrl, sessionId])

  return { messages, busy, send, retry, stop, clear }
}
