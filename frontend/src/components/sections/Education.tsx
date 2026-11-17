import { GraduationCap, Presentation } from 'lucide-react'
import { activities, education } from '../../data/experience'
import { Reveal } from '../ui/Reveal'
import { Section } from '../ui/Section'
import { Training } from './Training'

export function Education() {
  return (
    <Section id="education" eyebrow="06 · Education & Activities" title="Education, training, and teaching.">
      <div className="grid gap-5 lg:grid-cols-2">
        <Reveal>
          <div className="card h-full p-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
              <GraduationCap size={17} className="text-accent" aria-hidden="true" /> Education
            </h3>
            <ul className="mt-5 divide-y divide-line">
              {education.map((e) => (
                <li key={e.title} className="py-3.5 first:pt-0 last:pb-0">
                  <p className="font-medium text-fg">{e.title}</p>
                  {(e.institution || e.note) && (
                    <p className="mt-0.5 text-sm text-muted">
                      {[e.institution, e.note].filter(Boolean).join(' · ')}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
        <Reveal delay={0.06}>
          <div className="card h-full p-6">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
              <Presentation size={17} className="text-accent" aria-hidden="true" /> Activities
            </h3>
            <ul className="mt-5 divide-y divide-line">
              {activities.map((a) => (
                <li key={a.title} className="py-3.5 first:pt-0 last:pb-0">
                  <p className="font-medium text-fg">{a.title}</p>
                  <p className="mt-0.5 text-sm text-muted">{a.note}</p>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
      <Training />
    </Section>
  )
}
