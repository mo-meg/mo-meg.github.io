import { AlertTriangle, Check, Copy, FileText, RotateCcw } from 'lucide-react'
import { useState } from 'react'
import Markdown, { type Components } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Source } from './api'
import type { ChatMessage } from './useChat'

const time = (ts: number) => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

/** Turns "[S2]" / "[S1, S3]" markers into in-text citation links resolved against the sources list. */
function linkCitations(text: string) {
  return text.replace(/\[(S\d+(?:\s*,\s*S\d+)*)\]/g, (_, ids: string) =>
    ids
      .split(',')
      .map((id) => id.trim())
      .map((id) => `[${id.slice(1)}](#cite-${id})`)
      .join(''),
  )
}

const RTL = /[֐-ࣿ]/

export function ChatMessageView({ message, onRetry }: { message: ChatMessage; onRetry: (id: string) => void }) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'
  const sourcesById = new Map((message.sources ?? []).map((s) => [s.id, s]))
  const dir = RTL.test(message.content.slice(0, 80)) ? 'rtl' : 'auto'

  const components: Components = {
    a({ href, children }) {
      if (href?.startsWith('#cite-')) {
        const src = sourcesById.get(href.slice(6))
        if (!src) return null // never show a citation we cannot resolve
        const cls =
          'mx-0.5 inline-grid h-4 min-w-4 place-items-center rounded bg-accent/15 px-1 align-text-top font-mono text-[10px] text-accent no-underline'
        return src.url ? (
          <a href={src.url} target="_blank" rel="noreferrer" title={src.label} className={cls}>
            {children}
          </a>
        ) : (
          <span title={src.label} className={cls}>
            {children}
          </span>
        )
      }
      return (
        <a href={href} target="_blank" rel="noreferrer">
          {children}
        </a>
      )
    },
  }

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content.replace(/\s?\[S\d+(?:\s*,\s*S\d+)*\]/g, ''))
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  if (isUser) {
    return (
      <div className="flex flex-col items-end">
        <div dir={dir} className="max-w-[85%] rounded-2xl rounded-br-md bg-accent/15 px-3.5 py-2 text-sm whitespace-pre-wrap text-fg">
          {message.content}
        </div>
        <span className="mt-1 px-1 text-[10px] text-subtle">{time(message.createdAt)}</span>
      </div>
    )
  }

  const waiting = message.streaming && !message.content

  return (
    <div className="flex flex-col items-start">
      <div className="w-full max-w-[92%] rounded-2xl rounded-bl-md border border-line bg-surface-strong px-3.5 py-2.5 text-fg">
        {waiting ? (
          <span className="flex items-center gap-1 py-1" role="status" aria-label="Assistant is typing">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted"
                style={{ animationDelay: `${i * 120}ms` }}
              />
            ))}
          </span>
        ) : (
          message.content && (
            <div className="prose-chat" dir={dir}>
              <Markdown remarkPlugins={[remarkGfm]} components={components}>
                {linkCitations(message.content)}
              </Markdown>
            </div>
          )
        )}

        {message.error && (
          <div className="mt-2 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
            <span className="flex-1">{message.error.message}</span>
            {message.error.retryable && (
              <button
                type="button"
                onClick={() => onRetry(message.id)}
                className="inline-flex shrink-0 items-center gap-1 font-medium underline-offset-2 hover:underline"
              >
                <RotateCcw size={12} aria-hidden="true" /> Retry
              </button>
            )}
          </div>
        )}

        {!message.streaming && message.sources && message.sources.length > 0 && (
          <SourceList sources={message.sources} />
        )}
      </div>

      <div className="mt-1 flex items-center gap-2 px-1 text-[10px] text-subtle">
        <span>{time(message.createdAt)}</span>
        {!message.streaming && message.content && (
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-1 rounded px-1 py-0.5 hover:text-fg"
            aria-label="Copy response"
          >
            {copied ? <Check size={11} aria-hidden="true" /> : <Copy size={11} aria-hidden="true" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        )}
      </div>
    </div>
  )
}

function SourceList({ sources }: { sources: Source[] }) {
  return (
    <div className="mt-3 border-t border-line pt-2.5">
      <p className="mb-1.5 text-[10px] font-medium tracking-wider text-subtle uppercase">Sources</p>
      <ul className="space-y-1">
        {sources.map((s) => (
          <li key={s.id} className="flex items-start gap-2 text-xs">
            <span className="mt-px font-mono text-[10px] text-accent">{s.id.slice(1)}</span>
            <FileText size={12} className="mt-0.5 shrink-0 text-subtle" aria-hidden="true" />
            {s.url ? (
              <a href={s.url} target="_blank" rel="noreferrer" className="text-muted underline-offset-2 hover:text-accent hover:underline">
                {s.label}
              </a>
            ) : (
              <span className="text-muted">{s.label}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
