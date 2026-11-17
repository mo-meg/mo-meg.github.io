import { Boxes, Briefcase, Cloud, FileSearch, GraduationCap, Languages, Workflow } from 'lucide-react'
import { profile } from '../../data/profile'
import { Reveal } from '../ui/Reveal'
import { Section } from '../ui/Section'

const pillars = [
  {
    icon: FileSearch,
    title: 'Retrieval & multimodal RAG',
    text: 'Retrieval systems over PDFs, images, tables, and video transcripts — with source attribution so answers can be verified.',
  },
  {
    icon: Workflow,
    title: 'NLP, speech & ML',
    text: 'Named entity recognition with spaCy, speech recognition and speaker diarization, and LLM-based text analysis.',
  },
  {
    icon: Boxes,
    title: 'Production AI pipelines',
    text: 'FastAPI services, asynchronous workers with Celery and Redis, vector storage in PostgreSQL/pgvector, and monitoring with Prometheus and Grafana.',
  },
  {
    icon: Cloud,
    title: 'Cloud & containers',
    text: 'Containerized architectures with Docker and Docker Compose, deployed on AWS and Google Cloud Platform.',
  },
  {
    icon: Briefcase,
    title: 'Business ↔ AI',
    text: 'A Business Informatics background: translating business requirements into concrete AI use cases and integrating them into existing systems such as CRMs.',
  },
]

export function About() {
  return (
    <Section id="about" eyebrow="01 · About" title="An engineer who ships AI systems end to end.">
      <div className="grid gap-12 lg:grid-cols-[1.1fr_1fr]">
        <Reveal className="space-y-5 text-[15.5px] leading-relaxed text-muted">
          <p>
            I hold a <span className="text-fg">Master’s degree in Business Informatics</span> (M.Sc. Information Systems) from
            FernUniversität in Hagen, and I work on the part of AI that happens after the notebook: turning models into systems
            that ingest real data, run reliably, and integrate with the software people already use.
          </p>
          <p>
            My recent work centres on <span className="text-fg">retrieval-augmented generation</span> — including a multimodal
            RAG system for Moodle that retrieves across course PDFs, embedded figures, and lecture videos — and on
            <span className="text-fg"> speech and language pipelines</span> that turn sales conversations into structured insight
            inside CRM systems.
          </p>
          <p>
            My engineering approach is pragmatic: keep retrieval and generation separable, make every answer traceable to its
            sources, move heavy work off the request path, measure before tuning, and prefer architectures that keep sensitive
            data under control.
          </p>

          <dl className="grid grid-cols-1 gap-4 pt-4 sm:grid-cols-2">
            <div className="card p-4">
              <dt className="flex items-center gap-2 text-xs font-medium tracking-wide text-subtle uppercase">
                <GraduationCap size={14} aria-hidden="true" /> Education
              </dt>
              <dd className="mt-2 text-sm text-fg">
                M.Sc. Information Systems
                <br />
                <span className="text-muted">FernUniversität in Hagen · 2025</span>
              </dd>
            </div>
            <div className="card p-4">
              <dt className="flex items-center gap-2 text-xs font-medium tracking-wide text-subtle uppercase">
                <Languages size={14} aria-hidden="true" /> Languages
              </dt>
              <dd className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
                {profile.languages.map((l) => (
                  <span key={l.name} className="text-fg">
                    {l.name} <span className="text-muted">· {l.level}</span>
                  </span>
                ))}
              </dd>
            </div>
          </dl>
        </Reveal>

        <ul className="grid gap-3">
          {pillars.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.05}>
              <li className="card flex gap-4 p-4 transition-colors hover:border-line-strong">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-line bg-accent/10 text-accent">
                  <p.icon size={17} aria-hidden="true" />
                </span>
                <div>
                  <h3 className="text-sm font-semibold text-fg">{p.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted">{p.text}</p>
                </div>
              </li>
            </Reveal>
          ))}
        </ul>
      </div>
    </Section>
  )
}
