import { Award, BadgeCheck, ChevronDown, FileText } from 'lucide-react'
import { useState } from 'react'
import { training, trainingTopics, type TrainingEntry } from '../../data/training'
import { asset } from '../../lib/config'
import { Reveal } from '../ui/Reveal'

function link(e: TrainingEntry) {
  if (e.url) return { href: e.url, label: 'Verify', icon: BadgeCheck }
  if (e.pdf) return { href: asset(`certificates/${e.pdf}`), label: 'PDF', icon: FileText }
  return null
}

function EntryLink({ e }: { e: TrainingEntry }) {
  const l = link(e)
  if (!l) return null
  return (
    <a
      href={l.href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 text-[11px] text-subtle hover:text-accent"
      aria-label={`${l.label}: ${e.title}`}
    >
      <l.icon size={12} aria-hidden="true" /> {l.label}
    </a>
  )
}

/** "Continuous learning": certifications first, a short highlighted list of courses, the rest behind a toggle. */
export function Training() {
  const [open, setOpen] = useState(false)
  const certifications = training.filter((t) => t.kind === 'certification')
  const courses = training.filter((t) => t.kind !== 'certification')
  const featured = courses.filter((t) => t.featured)
  const providers = [...new Set(courses.map((c) => c.provider))].join(', ')

  return (
    <Reveal className="mt-5">
      <div className="card p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
            <Award size={17} className="text-accent" aria-hidden="true" /> Continuous learning
          </h3>
          <p className="text-xs text-subtle">
            {courses.length} completed courses · {providers}
          </p>
        </div>

        {certifications.length > 0 && (
          <ul className="mt-5 grid gap-3 sm:grid-cols-2">
            {certifications.map((c) => (
              <li key={c.title} className="rounded-xl border border-accent/30 bg-accent/5 px-4 py-3">
                <p className="font-medium text-fg">{c.title}</p>
                <div className="mt-1 flex items-center gap-3 text-xs text-muted">
                  <span>
                    {c.provider}
                    {c.year ? ` · ${c.year}` : ''}
                  </span>
                  <EntryLink e={c} />
                </div>
              </li>
            ))}
          </ul>
        )}

        <p className="mt-5 text-xs tracking-wide text-subtle uppercase">Highlights</p>
        <ul className="mt-2 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {featured.map((c) => (
            <li key={c.title} className="flex items-center justify-between gap-3 border-b border-line pb-2 text-sm">
              <span className="text-fg">{c.title}</span>
              <EntryLink e={c} />
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-controls="all-training"
          className="mt-5 inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg"
        >
          <ChevronDown size={15} className={`transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden="true" />
          {open ? 'Hide' : 'Show'} all {courses.length} courses by topic
        </button>

        {open && (
          <div id="all-training" className="mt-4 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {trainingTopics.map((topic) => {
              const items = courses.filter((c) => c.topic === topic)
              if (!items.length) return null
              return (
                <div key={topic}>
                  <p className="font-mono text-[11px] tracking-[0.12em] text-accent uppercase">
                    {topic} <span className="text-subtle">· {items.length}</span>
                  </p>
                  <ul className="mt-2 space-y-1.5">
                    {items.map((c) => (
                      <li key={c.title} className="flex items-start justify-between gap-2 text-[13px] text-muted">
                        <span>{c.title}</span>
                        <EntryLink e={c} />
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </Reveal>
  )
}
