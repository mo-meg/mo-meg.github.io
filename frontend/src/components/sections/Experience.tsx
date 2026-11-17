import { experience } from '../../data/experience'
import { Reveal } from '../ui/Reveal'
import { Section } from '../ui/Section'

const kindStyle = {
  Professional: 'text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/10',
  Research: 'text-accent-3 border-accent-3/30 bg-accent-3/10',
  Academic: 'text-accent-2 border-accent-2/30 bg-accent-2/10',
} as const

export function Experience() {
  return (
    <Section id="experience" eyebrow="05 · Experience" title="Professional experience.">
      <ol className="relative ml-2 border-l border-line">
        {experience.map((e, i) => (
          <li key={`${e.role}-${e.organization}`} className="relative pb-12 pl-8 last:pb-0">
            <span
              aria-hidden="true"
              className="absolute top-1.5 -left-[7px] h-3.5 w-3.5 rounded-full border-2 border-bg bg-accent ring-4 ring-accent/15"
            />
            <Reveal delay={i * 0.05}>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <h3 className="text-lg font-semibold text-fg">{e.role}</h3>
                <span className="text-muted">· {e.organization}</span>
                <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${kindStyle[e.kind]}`}>{e.kind}</span>
                {e.period && <span className="font-mono text-xs text-subtle">{e.period}</span>}
              </div>
              <p className="mt-1.5 text-sm text-accent">{e.focus}</p>
              {e.kind === 'Academic' ? (
                <div className="mt-4">
                  <p className="text-xs tracking-wide text-subtle uppercase">Relevant subjects</p>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {e.points.map((p) => (
                      <li key={p} className="chip text-xs">
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                  {e.points.map((p) => (
                    <li key={p} className="card flex gap-3 px-4 py-3 text-sm leading-relaxed text-muted">
                      <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" aria-hidden="true" />
                      {p}
                    </li>
                  ))}
                </ul>
              )}
            </Reveal>
          </li>
        ))}
      </ol>
    </Section>
  )
}
