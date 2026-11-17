import { Bot, Send, Square, Trash2, X } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { ChatMessageView } from './ChatMessageView'
import { MAX_INPUT_CHARS, useChat } from './useChat'

const WELCOME =
  "Hi! I'm Mohamed's AI assistant. I can help you learn about his experience, AI projects, technical expertise, and professional background.\n\nWhat would you like to know?"

const SUGGESTIONS = [
  "Tell me about Mohamed's AI engineering experience.",
  'Explain his Multimodal RAG project.',
  'What technologies does he use?',
  'Tell me about his experience with LLMs and AI agents.',
  'What experience does he have with cloud infrastructure?',
  'How can I contact Mohamed?',
]

export default function ChatPanel({ apiUrl, onClose }: { apiUrl: string; onClose: () => void }) {
  const { messages, busy, send, retry, stop, clear } = useChat(apiUrl)
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const submit = (e?: FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || busy) return
    send(input)
    setInput('')
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-line px-4 py-3">
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-500/20 text-accent">
          <Bot size={17} aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 id="chat-title" className="text-sm font-semibold text-fg">
            Ask about Mohamed
          </h2>
          <p className="font-mono text-[10px] text-subtle">Powered by Gemini + RAG</p>
        </div>
        <button
          type="button"
          onClick={clear}
          disabled={messages.length === 0}
          className="grid h-8 w-8 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg disabled:opacity-40"
          aria-label="Clear conversation"
          title="Clear conversation"
        >
          <Trash2 size={15} />
        </button>
        <button
          type="button"
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg"
          aria-label="Close assistant"
        >
          <X size={17} />
        </button>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite" aria-relevant="additions">
        <div className="max-w-[92%] rounded-2xl rounded-bl-md border border-line bg-surface-strong px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-line text-fg">
          {WELCOME}
        </div>

        {messages.length === 0 && (
          <div className="space-y-1.5">
            <p className="px-1 text-[11px] text-subtle">Suggested questions</p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="block w-full rounded-xl border border-line px-3 py-2 text-left text-[13px] text-muted transition-colors hover:border-accent/50 hover:text-fg"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((m) => (
          <ChatMessageView key={m.id} message={m} onRetry={retry} />
        ))}
      </div>

      <form onSubmit={submit} className="border-t border-line p-3">
        <div className="flex items-end gap-2 rounded-xl border border-line-strong bg-bg-elevated px-3 py-2 focus-within:border-accent/60">
          <label htmlFor="chat-input" className="sr-only">
            Your question
          </label>
          <textarea
            id="chat-input"
            ref={inputRef}
            rows={1}
            value={input}
            maxLength={MAX_INPUT_CHARS}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask in English, Deutsch, or العربية…"
            className="max-h-32 min-h-[24px] flex-1 resize-none bg-transparent text-sm text-fg outline-none placeholder:text-subtle"
            dir="auto"
          />
          {busy ? (
            <button
              type="button"
              onClick={stop}
              className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-fg/10 text-fg"
              aria-label="Stop generating"
            >
              <Square size={13} />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent text-white transition-opacity disabled:opacity-30 dark:text-slate-950"
              aria-label="Send message"
            >
              <Send size={14} />
            </button>
          )}
        </div>
        <p className="mt-2 px-1 text-[10px] leading-snug text-subtle">
          Answers are generated by Google Gemini from Mohamed’s documents and may be imperfect. Please don’t share personal
          data. {input.length > MAX_INPUT_CHARS * 0.8 && `${input.length}/${MAX_INPUT_CHARS}`}
        </p>
      </form>
    </div>
  )
}
