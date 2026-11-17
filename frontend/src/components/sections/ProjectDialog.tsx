import { ArrowUpRight, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import type { Project } from '../../data/projects'
import { FlowPipeline } from '../diagrams/FlowPipeline'
import { GithubIcon } from '../ui/BrandIcons'
import { contextStyle } from './projectStyles'

/** Native <dialog> gives focus trapping, Esc-to-close and inert background for free. */
export function ProjectDialog({ project, onClose }: { project: Project | null; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (project && !d.open) {
      d.showModal()
      document.body.style.overflow = 'hidden'
    } else if (!project && d.open) {
      d.close()
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [project])

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      aria-labelledby="project-dialog-title"
      className="m-auto max-h-[90vh] w-[min(920px,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-line-strong bg-bg-elevated p-0 text-fg shadow-2xl backdrop:bg-black/60 backdrop:backdrop-blur-sm"
    >
      {project && (
        <div className="flex max-h-[90vh] flex-col">
          <header className="flex items-start justify-between gap-4 border-b border-line px-6 py-5">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${contextStyle[project.context]}`}>
                  {project.context}
                </span>
                {project.organization && <span className="text-xs text-subtle">{project.organization}</span>}
              </div>
              <h3 id="project-dialog-title" className="mt-3 text-xl font-semibold tracking-tight sm:text-2xl">
                {project.title}
              </h3>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg"
              aria-label="Close case study"
            >
              <X size={18} />
            </button>
          </header>

          <div className="space-y-8 overflow-y-auto px-6 py-6">
            <Block title="Problem">
              <p className="leading-relaxed text-muted">{project.problem}</p>
            </Block>

            <Block title="Architecture / workflow">
              <div className="overflow-x-auto rounded-xl border border-line bg-bg p-4">
                <FlowPipeline stages={project.flow} label={`${project.title} workflow`} />
              </div>
            </Block>

            <Block title="Technical solution">
              <ul className="space-y-2.5">
                {project.solution.map((s) => (
                  <li key={s} className="flex gap-3 leading-relaxed text-muted">
                    <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-accent" aria-hidden="true" />
                    {s}
                  </li>
                ))}
              </ul>
            </Block>

            <div className="grid gap-8 md:grid-cols-2">
              <Block title="Key engineering challenges">
                <ul className="space-y-2.5">
                  {project.challenges.map((c) => (
                    <li key={c} className="flex gap-3 text-sm leading-relaxed text-muted">
                      <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent-2" aria-hidden="true" />
                      {c}
                    </li>
                  ))}
                </ul>
              </Block>
              <div className="space-y-8">
                <Block title="My contribution">
                  <p className="text-sm leading-relaxed text-muted">{project.contribution}</p>
                </Block>
                <Block title="Technologies">
                  <ul className="flex flex-wrap gap-1.5">
                    {project.stack.map((s) => (
                      <li key={s} className="chip">
                        {s}
                      </li>
                    ))}
                  </ul>
                </Block>
              </div>
            </div>

            {project.media && project.media.length > 0 && (
              <Block title="Screenshots">
                <div className="grid gap-3">
                  {project.media.map((m) => (
                    <img
                      key={m.src}
                      src={m.src}
                      alt={m.alt}
                      loading="lazy"
                      className="w-full rounded-xl border border-line"
                    />
                  ))}
                </div>
              </Block>
            )}
          </div>

          {project.repo && (
            <footer className="border-t border-line px-6 py-4">
              <a href={project.repo} target="_blank" rel="noreferrer" className="btn-ghost">
                <GithubIcon size={16} /> View repository <ArrowUpRight size={14} aria-hidden="true" />
              </a>
            </footer>
          )}
        </div>
      )}
    </dialog>
  )
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h4 className="mb-3 font-mono text-[11px] tracking-[0.16em] text-subtle uppercase">{title}</h4>
      {children}
    </section>
  )
}
