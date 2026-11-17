import { MessageSquare, X } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { lazy, Suspense, useEffect, useState } from 'react'
import { config } from '../../lib/config'

// The panel (incl. the markdown renderer) is only downloaded when the chat is opened.
const ChatPanel = lazy(() => import('./ChatPanel'))

export function ChatWidget() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  if (config.qaCount === 0) return null

  return (
    <>
      <AnimatePresence>
        {open && (
          <motion.div
            role="dialog"
            aria-modal="false"
            aria-labelledby="chat-title"
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="fixed inset-x-2 top-2 bottom-2 z-50 overflow-hidden rounded-2xl border border-line-strong bg-bg-elevated/95 shadow-2xl shadow-black/30 backdrop-blur-xl sm:inset-auto sm:right-5 sm:bottom-24 sm:h-[min(640px,calc(100vh-8rem))] sm:w-[400px]"
          >
            <Suspense fallback={<div className="grid h-full place-items-center text-sm text-muted">Loading…</div>}>
              <ChatPanel onClose={() => setOpen(false)} />
            </Suspense>
          </motion.div>
        )}
      </AnimatePresence>

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={open ? 'Close AI assistant' : 'Open AI assistant'}
        className={`fixed right-5 bottom-5 z-50 h-14 items-center gap-2 rounded-full pr-5 pl-4 text-sm font-medium text-white shadow-xl shadow-cyan-900/30 transition-transform hover:scale-[1.03] ${
          open ? 'hidden sm:flex' : 'flex'
        }`}
        style={{ background: 'linear-gradient(135deg, #0891b2, #6d28d9)' }}
      >
        {open ? <X size={20} aria-hidden="true" /> : <MessageSquare size={20} aria-hidden="true" />}
        <span className="hidden sm:inline">{open ? 'Close' : 'Ask my AI assistant'}</span>
      </button>
    </>
  )
}
