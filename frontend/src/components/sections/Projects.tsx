import { ArrowUpRight, Layers } from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import { useMemo, useState } from 'react'
import { projectCategories, projects, type Project, type ProjectCategory } from '../../data/projects'
import { FlowPipeline } from '../diagrams/FlowPipeline'
import { GithubIcon } from '../ui/BrandIcons'
import { Reveal } from '../ui/Reveal'
import { Section } from '../ui/Section'
import { ProjectDialog } from './ProjectDialog'
import { contextStyle } from './projectStyles'

type Filter = 'All' | ProjectCategory

export function Projects() {
  const [filter, setFilter] = useState<Filter>('All')
  const [open, setOpen] = useState<Project | null>(null)

  const visible = useMemo(
    () => (filter === 'All' ? projects : projects.filter((p) => p.categories.includes(filter))),
    [filter],
  )

  return (
    <Section
      id="projects"
      eyebrow="03 · Featured Projects"
      title="Case studies, not just repositories."
      intro="Each project is described by the problem, the architecture, the engineering challenges, and my role. Professional, academic, and personal work are labelled as such."
    >
      <div role="toolbar" aria-label="Filter projects by category" className="mb-8 flex flex-wrap gap-2">
        {(['All', ...projectCategories] as Filter[]).map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setFilter(c)}
            aria-pressed={filter === c}
            className={`rounded-full border px-3.5 py-1.5 text-sm transition-colors ${
              filter === c
                ? 'border-accent/60 bg-accent/10 text-fg'
                : 'border-line text-muted hover:border-line-strong hover:text-fg'
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      <motion.div layout className="grid gap-5 lg:grid-cols-2">
        <AnimatePresence mode="popLayout">
          {visible.map((p, i) => (
            <motion.article
              key={p.id}
              layout
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.25 }}
              className={`card group flex flex-col p-6 transition-colors hover:border-line-strong ${
                i === 0 && filter === 'All' ? 'lg:col-span-2' : ''
              }`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${contextStyle[p.context]}`}>
                  {p.context}
                </span>
                {p.organization && <span className="text-xs text-subtle">{p.organization}</span>}
              </div>

              <h3 className="mt-4 text-xl font-semibold tracking-tight text-fg">{p.title}</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-muted">{p.short}</p>

              <div className="mt-5 overflow-x-auto pb-1">
                <FlowPipeline stages={i === 0 && filter === 'All' ? p.flow : p.flow.slice(0, 4)} label={`${p.title} workflow`} />
                {!(i === 0 && filter === 'All') && p.flow.length > 4 && (
                  <p className="mt-2 font-mono text-[11px] text-subtle">+ {p.flow.length - 4} more stages</p>
                )}
              </div>

              <ul className="mt-5 flex flex-wrap gap-1.5" aria-label="Technologies">
                {p.stack.slice(0, 9).map((s) => (
                  <li key={s} className="chip">
                    {s}
                  </li>
                ))}
                {p.stack.length > 9 && <li className="chip">+{p.stack.length - 9}</li>}
              </ul>

              <div className="mt-auto flex flex-wrap items-center gap-2 pt-6">
                <button type="button" className="btn-primary py-2" onClick={() => setOpen(p)}>
                  <Layers size={15} aria-hidden="true" /> Read case study
                </button>
                {p.repo && (
                  <a href={p.repo} target="_blank" rel="noreferrer" className="btn-ghost py-2">
                    <GithubIcon size={15} /> Repository <ArrowUpRight size={14} aria-hidden="true" />
                  </a>
                )}
              </div>
            </motion.article>
          ))}
        </AnimatePresence>
      </motion.div>

      <Reveal className="mt-8 text-sm text-muted">
        More code on{' '}
        <a href="https://github.com/mmm-megahed" target="_blank" rel="noreferrer" className="text-accent underline-offset-4 hover:underline">
          github.com/mmm-megahed
        </a>
        .
      </Reveal>

      <ProjectDialog project={open} onClose={() => setOpen(null)} />
    </Section>
  )
}
