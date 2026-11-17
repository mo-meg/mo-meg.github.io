export interface Source {
  id: string // "S1"
  title: string
  label: string
  url?: string | null
  category?: string | null
}

export type StreamEvent =
  | { type: 'meta'; sessionId: string }
  | { type: 'delta'; text: string }
  | { type: 'sources'; sources: Source[] }
  | { type: 'done' }
  | { type: 'error'; message: string; retryable: boolean }

export class ChatApiError extends Error {
  readonly retryable: boolean
  constructor(message: string, retryable: boolean) {
    super(message)
    this.retryable = retryable
  }
}

/**
 * POSTs a message and yields Server-Sent Events from the streaming response.
 * (EventSource only supports GET, so the SSE stream is parsed manually.)
 */
export async function* streamChat(
  baseUrl: string,
  body: { message: string; session_id?: string | null },
  signal: AbortSignal,
): AsyncGenerator<StreamEvent> {
  let res: Response
  try {
    res = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify(body),
      signal,
    })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ChatApiError('The assistant is currently unreachable. Please try again in a moment.', true)
  }

  if (!res.ok || !res.body) {
    let detail = ''
    try {
      const j = await res.json()
      detail = typeof j?.detail === 'string' ? j.detail : j?.detail?.message ?? ''
    } catch {
      /* non-JSON error body */
    }
    if (res.status === 429) throw new ChatApiError(detail || 'Too many requests — please wait a moment and try again.', true)
    if (res.status === 413 || res.status === 422) throw new ChatApiError(detail || 'That message could not be processed. Try a shorter question.', false)
    throw new ChatApiError(detail || `The assistant returned an error (${res.status}).`, res.status >= 500)
  }

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += value
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      const evt = parseEvent(raw)
      if (evt) yield evt
    }
  }
}

function parseEvent(raw: string): StreamEvent | null {
  let event = 'message'
  const data: string[] = []
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''))
  }
  if (!data.length) return null
  let payload: Record<string, unknown>
  try {
    payload = JSON.parse(data.join('\n'))
  } catch {
    return null
  }
  switch (event) {
    case 'meta':
      return { type: 'meta', sessionId: String(payload.session_id ?? '') }
    case 'delta':
      return { type: 'delta', text: String(payload.text ?? '') }
    case 'sources':
      return { type: 'sources', sources: (payload.sources as Source[]) ?? [] }
    case 'done':
      return { type: 'done' }
    case 'error':
      return { type: 'error', message: String(payload.message ?? 'Unknown error'), retryable: Boolean(payload.retryable) }
    default:
      return null
  }
}

export async function resetSession(baseUrl: string, sessionId: string) {
  try {
    await fetch(`${baseUrl}/api/chat/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    })
  } catch {
    /* best effort — the server session also expires on its own */
  }
}
