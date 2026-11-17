import { ArrowUpRight, Check, Copy, Mail, MapPin } from 'lucide-react'
import { useState } from 'react'
import { profile } from '../../data/profile'
import { GithubIcon, LinkedinIcon } from '../ui/BrandIcons'
import { Reveal } from '../ui/Reveal'

export function Contact() {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(profile.email)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      /* clipboard blocked — the mailto link still works */
    }
  }

  const links = [
    { href: profile.github, label: 'GitHub', value: 'github.com/mo-meg', icon: <GithubIcon size={18} /> },
    {
      href: profile.githubAcademic,
      label: 'GitHub · academic projects',
      value: 'github.com/mmm-megahed',
      icon: <GithubIcon size={18} />,
    },
    { href: profile.linkedin, label: 'LinkedIn', value: 'in/mohamed-megahed-WiInfo', icon: <LinkedinIcon size={18} /> },
  ]

  return (
    <section id="contact" aria-labelledby="contact-title" className="relative py-20 sm:py-28">
      <div className="container-page">
        <Reveal>
          <div className="card relative overflow-hidden px-6 py-12 sm:px-12 sm:py-16">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute -top-32 -right-32 h-80 w-80 rounded-full opacity-25 blur-3xl"
              style={{ background: 'radial-gradient(closest-side, var(--accent), transparent)' }}
            />
            <p className="eyebrow">07 · Contact</p>
            <h2 id="contact-title" className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
              Building something with LLMs, retrieval, or ML? Let’s talk.
            </h2>
            <p className="mt-4 max-w-xl text-muted">
              I’m open to AI Engineer, RAG / LLM Engineer, and Machine Learning Engineer roles, and to conversations about
              AI systems. Email is the fastest way to reach me.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a href={`mailto:${profile.email}`} className="btn-primary">
                <Mail size={16} aria-hidden="true" /> {profile.email}
              </a>
              <button type="button" onClick={copy} className="btn-ghost" aria-live="polite">
                {copied ? <Check size={15} aria-hidden="true" /> : <Copy size={15} aria-hidden="true" />}
                {copied ? 'Copied' : 'Copy email'}
              </button>
            </div>

            <ul className="mt-10 grid gap-3 sm:grid-cols-2">
              {links.map((l) => (
                <li key={l.label}>
                  <a
                    href={l.href}
                    target="_blank"
                    rel="noreferrer"
                    className="group flex items-center gap-3 rounded-xl border border-line bg-bg-elevated/50 px-4 py-3 transition-colors hover:border-accent/50"
                  >
                    <span className="text-muted group-hover:text-fg">{l.icon}</span>
                    <span className="min-w-0">
                      <span className="block text-xs text-subtle">{l.label}</span>
                      <span className="block truncate text-sm text-fg">{l.value}</span>
                    </span>
                    <ArrowUpRight size={15} className="ml-auto text-subtle group-hover:text-accent" aria-hidden="true" />
                  </a>
                </li>
              ))}
              <li className="flex items-center gap-3 rounded-xl border border-line bg-bg-elevated/50 px-4 py-3">
                <MapPin size={18} className="text-muted" aria-hidden="true" />
                <span>
                  <span className="block text-xs text-subtle">Location</span>
                  <span className="block text-sm text-fg">{profile.location}</span>
                </span>
              </li>
            </ul>
          </div>
        </Reveal>
      </div>
    </section>
  )
}
