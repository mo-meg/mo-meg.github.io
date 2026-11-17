import { Bot, LayoutList, Send, Trash2, X } from 'lucide-react'
import qaItems from 'virtual:qa'
import { useEffect, useMemo, useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { browserLang, ui } from '../../qa/i18n'
import { Matcher } from '../../qa/matcher'
import { CATEGORIES, LANGS, type Category, type Lang, type PublishedItem } from '../../qa/types'
import { ChatMessageView, type ChatMsg } from './ChatMessageView'

const STORE_KEY = 'mm-qa-chat'
const MAX_INPUT = 500
const uid = () => Math.random().toString(36).slice(2, 10)

interface Stored {
  lang: Lang
  messages: ChatMsg[]
}

function load(): Stored {
  try {
    const raw = sessionStorage.getItem(STORE_KEY)
    if (raw) return JSON.parse(raw) as Stored
  } catch {
    /* ignore */
  }
  return { lang: browserLang(), messages: [] }
}

export default function ChatPanel({ onClose }: { onClose: () => void }) {
  const [initial] = useState(load)
  const [lang, setLang] = useState<Lang>(initial.lang)
  const [messages, setMessages] = useState<ChatMsg[]>(initial.messages)
  const [browsing, setBrowsing] = useState(initial.messages.length === 0)
  const [input, setInput] = useState('')
  const matcher = useMemo(() => new Matcher(qaItems), [])
  const categories = useMemo(() => CATEGORIES.filter((c) => qaItems.some((i) => i.category === c)), [])
  const [category, setCategory] = useState<Category>(categories[0] ?? 'profile')
  const scrollRef = useRef<HTMLDivElement>(null)
  const t = ui[lang]

  useEffect(() => {
    try {
      sessionStorage.setItem(STORE_KEY, JSON.stringify({ lang, messages }))
    } catch {
      /* storage unavailable */
    }
  }, [lang, messages])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messages, browsing])

  const ask = (item: PublishedItem, answerLang: Lang) => {
    const now = Date.now()
    setBrowsing(false)
    setMessages((ms) => [
      ...ms,
      { id: uid(), role: 'user', text: item.i18n[answerLang].question, createdAt: now },
      { id: uid(), role: 'answer', itemId: item.id, lang: answerLang, createdAt: now },
    ])
  }

  const submit = (e?: FormEvent) => {
    e?.preventDefault()
    const text = input.trim().slice(0, MAX_INPUT)
    if (!text) return
    const result = matcher.match(text, lang)
    const now = Date.now()
    setBrowsing(false)
    setInput('')
    setMessages((ms) => [
      ...ms,
      { id: uid(), role: 'user', text, createdAt: now },
      result.best
        ? { id: uid(), role: 'answer', itemId: result.best.item.id, lang: result.lang, createdAt: now }
        : {
            id: uid(),
            role: 'fallback',
            query: text,
            lang: result.lang,
            suggestions: result.suggestions.map((s) => s.id),
            createdAt: now,
          },
    ])
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  const clear = () => {
    setMessages([])
    setBrowsing(true)
  }

  // Section links close the panel so the page is visible (the panel is full-screen on mobile).
  const navigate = () => onClose()

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-line px-4 py-3" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-violet-500/20 text-accent">
          <Bot size={17} aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 id="chat-title" className="text-sm font-semibold text-fg">
            {t.title}
          </h2>
          <p className="truncate font-mono text-[10px] text-subtle">{t.subtitle}</p>
        </div>
        <div role="group" aria-label="Language" className="flex rounded-md border border-line p-0.5" dir="ltr">
          {LANGS.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => setLang(l)}
              aria-pressed={lang === l}
              title={ui[l].langName}
              className={`rounded px-1.5 py-0.5 font-mono text-[10px] uppercase transition-colors ${
                lang === l ? 'bg-accent/15 text-fg' : 'text-subtle hover:text-fg'
              }`}
            >
              {l}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={clear}
          disabled={messages.length === 0}
          className="grid h-8 w-8 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg disabled:opacity-40"
          aria-label={t.clear}
          title={t.clear}
        >
          <Trash2 size={15} />
        </button>
        <button
          type="button"
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg"
          aria-label={t.close}
        >
          <X size={17} />
        </button>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite" aria-relevant="additions">
        <div
          dir={lang === 'ar' ? 'rtl' : 'ltr'}
          className="max-w-[92%] rounded-2xl rounded-es-md border border-line bg-surface-strong px-3.5 py-2.5 text-sm leading-relaxed text-fg"
        >
          {t.welcome}
        </div>

        {messages.map((m) => (
          <ChatMessageView key={m.id} msg={m} getItem={(id) => matcher.get(id)} onAsk={ask} onNavigate={navigate} />
        ))}

        {browsing ? (
          <div dir={lang === 'ar' ? 'rtl' : 'ltr'} className="space-y-2">
            <p className="px-1 text-[11px] text-subtle">{t.suggested}</p>
            <div role="tablist" aria-label={t.suggested} className="flex flex-wrap gap-1.5">
              {categories.map((c) => (
                <button
                  key={c}
                  role="tab"
                  type="button"
                  aria-selected={category === c}
                  onClick={() => setCategory(c)}
                  className={`rounded-full border px-2.5 py-1 text-[11px] transition-colors ${
                    category === c ? 'border-accent/60 bg-accent/10 text-fg' : 'border-line text-muted hover:text-fg'
                  }`}
                >
                  {t.categories[c]}
                </button>
              ))}
            </div>
            <ul role="tabpanel" className="space-y-1.5">
              {qaItems
                .filter((i) => i.category === category)
                .map((i) => (
                  <li key={i.id}>
                    <button
                      type="button"
                      onClick={() => ask(i, lang)}
                      className="block w-full rounded-xl border border-line px-3 py-2 text-start text-[13px] text-muted transition-colors hover:border-accent/50 hover:text-fg"
                    >
                      {i.i18n[lang].question}
                      {i.status !== 'approved' && <span className="ms-2 font-mono text-[9px] text-amber-500">draft</span>}
                    </button>
                  </li>
                ))}
            </ul>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setBrowsing(true)}
            className="mx-auto flex items-center gap-1.5 rounded-full border border-line px-3 py-1 text-[11px] text-muted hover:text-fg"
          >
            <LayoutList size={12} aria-hidden="true" /> {t.back}
          </button>
        )}
      </div>

      <form onSubmit={submit} className="border-t border-line p-3">
        <div className="flex items-end gap-2 rounded-xl border border-line-strong bg-bg-elevated px-3 py-2 focus-within:border-accent/60">
          <label htmlFor="chat-input" className="sr-only">
            {t.placeholder}
          </label>
          <textarea
            id="chat-input"
            rows={1}
            value={input}
            maxLength={MAX_INPUT}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={t.placeholder}
            className="max-h-32 min-h-[24px] flex-1 resize-none bg-transparent text-sm text-fg outline-none placeholder:text-subtle"
            dir="auto"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-accent text-white transition-opacity disabled:opacity-30 dark:text-slate-950"
            aria-label={t.send}
          >
            <Send size={14} />
          </button>
        </div>
        <p className="mt-2 px-1 text-[10px] leading-snug text-subtle" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
          {t.footer}
        </p>
      </form>
    </div>
  )
}
