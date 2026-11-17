import { skillGroups } from '../../data/skills'
import { Reveal } from '../ui/Reveal'
import { Section } from '../ui/Section'

export function Expertise() {
  return (
    <Section
      id="expertise"
      eyebrow="02 · Technical Expertise"
      title="The stack behind the systems."
      intro="Grouped by where it sits in an AI system — from models and retrieval down to the infrastructure that runs them."
    >
      <div className="grid gap-4 md:grid-cols-2">
        {skillGroups.map((g, i) => (
          <Reveal key={g.title} delay={i * 0.06}>
            <article className="card group relative h-full overflow-hidden p-6 transition-colors hover:border-line-strong">
              <div
                aria-hidden="true"
                className="pointer-events-none absolute -top-24 -right-24 h-48 w-48 rounded-full opacity-0 blur-3xl transition-opacity duration-500 group-hover:opacity-30"
                style={{ background: 'var(--accent)' }}
              />
              <div className="flex items-start gap-4">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-line bg-accent/10 text-accent">
                  <g.icon size={19} aria-hidden="true" />
                </span>
                <div>
                  <h3 className="font-semibold text-fg">{g.title}</h3>
                  <p className="mt-0.5 text-sm text-muted">{g.description}</p>
                </div>
              </div>
              <ul className="mt-5 flex flex-wrap gap-2" aria-label={`${g.title} skills`}>
                {g.skills.map((s) => (
                  <li
                    key={s}
                    className="rounded-lg border border-line bg-bg-elevated/60 px-2.5 py-1 text-[13px] text-fg/90 transition-colors hover:border-accent/50"
                  >
                    {s}
                  </li>
                ))}
              </ul>
            </article>
          </Reveal>
        ))}
      </div>
    </Section>
  )
}
