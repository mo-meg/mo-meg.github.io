import { ArrowUpRight, Check, Copy, FileText, Mail } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { useState, type ReactNode } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { profile } from '../../data/profile'
import { ui } from '../../qa/i18n'
import type { Lang, PublishedItem } from '../../qa/types'
import { LinkedinIcon } from '../ui/BrandIcons'

export type ChatMsg =
  | { id: string; role: 'user'; text: string; createdAt: number }
  | { id: string; role: 'answer'; itemId: string; lang: Lang; createdAt: number }
  | { id: string; role: 'fallback'; query: string; lang: Lang; suggestions: string[]; createdAt: number }

const time = (ts: number) => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
const isRtl = (text: string) => /[֐-ࣿ]/.test(text.slice(0, 60))

interface Props {
  msg: ChatMsg
  getItem: (id: string) => PublishedItem | undefined
  onAsk: (item: PublishedItem, lang: Lang) => void
  onNavigate: () => void
}

/** Short reveal (<300 ms) — no fake typing; these are prepared answers. */
function Reveal({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion()
  return (
    <motion.div initial={reduce ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
      {children}
    </motion.div>
  )
}

function SourceLink({ href, label, onNavigate }: { href: string; label: string; onNavigate: () => void }) {
  const internal = href.startsWith('#')
  return (
    <a
      href={href}
      onClick={internal ? onNavigate : undefined}
      target={internal ? undefined : '_blank'}
      rel={internal ? undefined : 'noreferrer'}
      className="inline-flex items-center gap-1.5 text-muted underline-offset-2 hover:text-accent hover:underline"
    >
      <FileText size={12} className="shrink-0 text-subtle" aria-hidden="true" />
      {label}
      {!internal && <ArrowUpRight size={11} aria-hidden="true" />}
    </a>
  )
}

function QuestionChips({ ids, lang, getItem, onAsk }: { ids: string[]; lang: Lang; getItem: Props['getItem']; onAsk: Props['onAsk'] }) {
  const items = ids.map(getItem).filter((i): i is PublishedItem => !!i)
  if (!items.length) return null
  return (
    <ul className="flex flex-col gap-1.5">
      {items.map((it) => (
        <li key={it.id}>
          <button
            type="button"
            onClick={() => onAsk(it, lang)}
            dir={lang === 'ar' ? 'rtl' : 'ltr'}
            className="w-full rounded-lg border border-line px-2.5 py-1.5 text-start text-xs text-muted transition-colors hover:border-accent/50 hover:text-fg"
          >
            {it.i18n[lang].question}
          </button>
        </li>
      ))}
    </ul>
  )
}

export function ChatMessageView({ msg, getItem, onAsk, onNavigate }: Props) {
  const [copied, setCopied] = useState(false)

  if (msg.role === 'user') {
    return (
      <div className="flex flex-col items-end">
        <div
          dir={isRtl(msg.text) ? 'rtl' : 'auto'}
          className="max-w-[85%] rounded-2xl rounded-ee-md bg-accent/15 px-3.5 py-2 text-sm whitespace-pre-wrap text-fg"
        >
          {msg.text}
        </div>
        <span className="mt-1 px-1 text-[10px] text-subtle">{time(msg.createdAt)}</span>
      </div>
    )
  }

  const t = ui[msg.lang]
  const dir = msg.lang === 'ar' ? 'rtl' : 'ltr'

  if (msg.role === 'fallback') {
    const mailto = `mailto:${profile.email}?subject=${encodeURIComponent(t.emailSubject)}&body=${encodeURIComponent(t.emailBody(msg.query))}`
    return (
      <Reveal>
        <div dir={dir} className="w-full max-w-[92%] rounded-2xl rounded-es-md border border-line bg-surface-strong px-3.5 py-3 text-sm text-fg">
          <p className="leading-relaxed">{t.fallback}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <a href={mailto} className="btn-primary px-3 py-1.5 text-xs">
              <Mail size={13} aria-hidden="true" /> {t.emailMe}
            </a>
            <a href={profile.linkedin} target="_blank" rel="noreferrer" className="btn-ghost px-3 py-1.5 text-xs">
              <LinkedinIcon size={13} /> {t.linkedin}
            </a>
          </div>
          {msg.suggestions.length > 0 && (
            <div className="mt-3 border-t border-line pt-2.5">
              <p className="mb-1.5 text-[10px] font-medium tracking-wider text-subtle uppercase">{t.didYouMean}</p>
              <QuestionChips ids={msg.suggestions} lang={msg.lang} getItem={getItem} onAsk={onAsk} />
            </div>
          )}
        </div>
        <span className="mt-1 block px-1 text-[10px] text-subtle">{time(msg.createdAt)}</span>
      </Reveal>
    )
  }

  const item = getItem(msg.itemId)
  if (!item) return null
  const loc = item.i18n[msg.lang]

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(loc.answer)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <Reveal>
      <div dir={dir} className="w-full max-w-[92%] rounded-2xl rounded-es-md border border-line bg-surface-strong px-3.5 py-2.5 text-fg">
        {item.status !== 'approved' && (
          <p className="mb-2 inline-block rounded bg-amber-500/15 px-1.5 py-0.5 font-mono text-[10px] text-amber-700 dark:text-amber-300">
            {t.draft} ({item.status})
          </p>
        )}
        <div className="prose-chat">
          <Markdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children }) =>
                href?.startsWith('#') ? (
                  <a href={href} onClick={onNavigate}>
                    {children}
                  </a>
                ) : (
                  <a href={href} target="_blank" rel="noreferrer">
                    {children}
                  </a>
                ),
            }}
          >
            {loc.answer}
          </Markdown>
        </div>

        {item.sources.length > 0 && (
          <div className="mt-3 border-t border-line pt-2.5">
            <p className="mb-1.5 text-[10px] font-medium tracking-wider text-subtle uppercase">{t.sources}</p>
            <ul className="space-y-1 text-xs">
              {item.sources.map((s) => (
                <li key={s.href + s.label}>
                  <SourceLink href={s.href} label={s.label} onNavigate={onNavigate} />
                </li>
              ))}
            </ul>
          </div>
        )}

        {item.related.length > 0 && (
          <div className="mt-3 border-t border-line pt-2.5">
            <p className="mb-1.5 text-[10px] font-medium tracking-wider text-subtle uppercase">{t.related}</p>
            <QuestionChips ids={item.related} lang={msg.lang} getItem={getItem} onAsk={onAsk} />
          </div>
        )}
      </div>
      <div className="mt-1 flex items-center gap-2 px-1 text-[10px] text-subtle">
        <span>{time(msg.createdAt)}</span>
        <button type="button" onClick={copy} className="inline-flex items-center gap-1 rounded px-1 py-0.5 hover:text-fg" aria-label={t.copy}>
          {copied ? <Check size={11} aria-hidden="true" /> : <Copy size={11} aria-hidden="true" />}
          {copied ? t.copied : t.copy}
        </button>
      </div>
    </Reveal>
  )
}
