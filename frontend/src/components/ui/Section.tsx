import type { ReactNode } from 'react'
import { Reveal } from './Reveal'

interface SectionProps {
  id: string
  eyebrow: string
  title: string
  intro?: ReactNode
  children: ReactNode
  className?: string
}

export function Section({ id, eyebrow, title, intro, children, className = '' }: SectionProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className={`relative py-20 sm:py-28 ${className}`}>
      <div className="container-page">
        <Reveal>
          <p className="eyebrow">{eyebrow}</p>
          <h2 id={`${id}-title`} className="mt-3 text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
            {title}
          </h2>
          {intro && <div className="mt-4 max-w-2xl text-base leading-relaxed text-muted">{intro}</div>}
        </Reveal>
        <div className="mt-12">{children}</div>
      </div>
    </section>
  )
}
