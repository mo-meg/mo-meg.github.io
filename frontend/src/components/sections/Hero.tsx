import { ArrowRight, Download, GraduationCap, Mail, MapPin } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { profile } from '../../data/profile'
import { config } from '../../lib/config'
import { GithubIcon, LinkedinIcon } from '../ui/BrandIcons'
import { NeuralBackground } from './NeuralBackground'

const trace = [
  { k: 'query', v: '"What AI systems has Mohamed built?"' },
  { k: 'embed', v: 'task=RETRIEVAL_QUERY' },
  { k: 'retrieve', v: 'pgvector ∪ full-text → RRF → top_k' },
  { k: 'ground', v: 'context = numbered, untrusted sources' },
  { k: 'generate', v: 'LLM → streamed answer + [S1] [S2]' },
]

export function Hero() {
  const reduce = useReducedMotion()
  const fade = (delay: number) =>
    reduce
      ? {}
      : {
          initial: { opacity: 0, y: 14 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
        }

  return (
    <section id="top" className="relative isolate overflow-hidden pt-28 pb-20 sm:pt-36 sm:pb-28">
      <div className="absolute inset-0 -z-10">
        <div className="grid-bg absolute inset-0" />
        <NeuralBackground />
        <div
          className="absolute -top-40 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full opacity-25 blur-3xl dark:opacity-20"
          style={{ background: 'radial-gradient(closest-side, var(--accent-2), transparent)' }}
        />
        <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-bg" />
      </div>

      <div className="container-page grid items-center gap-14 lg:grid-cols-[1.25fr_1fr]">
        <div>
          <motion.div {...fade(0)} className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted">
            <span className="inline-flex items-center gap-2 rounded-full border border-line-strong bg-surface px-3 py-1 font-mono text-xs text-fg">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
              {profile.name} · {profile.role}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <MapPin size={14} aria-hidden="true" /> {profile.location}
            </span>
          </motion.div>

          <motion.h1
            {...fade(0.08)}
            className="mt-6 text-4xl leading-[1.05] font-semibold tracking-tight text-balance sm:text-6xl lg:text-[4.1rem]"
          >
            <span className="text-gradient">{profile.headline}</span>
          </motion.h1>

          <motion.p {...fade(0.16)} className="mt-6 max-w-xl text-lg leading-relaxed text-fg/90">
            {profile.subheadline}
          </motion.p>

          <motion.p {...fade(0.22)} className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted">
            {profile.intro}
          </motion.p>

          <motion.div {...fade(0.28)} className="mt-5 flex items-center gap-2 text-sm text-muted">
            <GraduationCap size={16} className="text-accent" aria-hidden="true" />
            Master’s degree in Business Informatics · {profile.university}
          </motion.div>

          <motion.div {...fade(0.34)} className="mt-9 flex flex-wrap items-center gap-3">
            <a href="#projects" className="btn-primary">
              Explore My Projects <ArrowRight size={16} aria-hidden="true" />
            </a>
            {config.cvUrl && (
              <a href={config.cvUrl} className="btn-ghost" download>
                <Download size={16} aria-hidden="true" /> Download CV
              </a>
            )}
            <a href="#contact" className="btn-ghost">
              <Mail size={16} aria-hidden="true" /> Get in Touch
            </a>
            <div className="ml-1 flex items-center gap-1">
              <a
                href={profile.github}
                target="_blank"
                rel="noreferrer"
                className="grid h-10 w-10 place-items-center rounded-lg text-muted transition-colors hover:text-fg"
                aria-label="GitHub profile"
              >
                <GithubIcon />
              </a>
              <a
                href={profile.linkedin}
                target="_blank"
                rel="noreferrer"
                className="grid h-10 w-10 place-items-center rounded-lg text-muted transition-colors hover:text-fg"
                aria-label="LinkedIn profile"
              >
                <LinkedinIcon />
              </a>
            </div>
          </motion.div>
        </div>

        <motion.div {...fade(0.3)} className="hidden md:block" aria-hidden="true">
          <div className="card overflow-hidden shadow-2xl shadow-black/20">
            <div className="flex items-center gap-2 border-b border-line px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-fg/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-fg/15" />
              <span className="h-2.5 w-2.5 rounded-full bg-fg/15" />
              <span className="ml-3 font-mono text-[11px] text-subtle">rag.pipeline — trace</span>
            </div>
            <ol className="space-y-3 p-5 font-mono text-[12.5px] leading-relaxed">
              {trace.map((t, i) => (
                <motion.li
                  key={t.k}
                  initial={reduce ? false : { opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + i * 0.18, duration: 0.4 }}
                  className="grid grid-cols-[5.5rem_1fr] gap-3"
                >
                  <span className="text-accent">{t.k}</span>
                  <span className="text-muted">{t.v}</span>
                </motion.li>
              ))}
              <motion.li
                initial={reduce ? false : { opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 + trace.length * 0.18 }}
                className="flex items-center gap-2 pt-2 text-fg"
              >
                <span className="text-emerald-500">✓</span> grounded answer with sources
                <span className="ml-0.5 inline-block h-4 w-[7px] animate-pulse bg-accent/70" />
              </motion.li>
            </ol>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
