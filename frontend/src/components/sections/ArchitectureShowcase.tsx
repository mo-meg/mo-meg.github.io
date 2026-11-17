import { AnimatePresence, motion } from 'motion/react'
import { MousePointerClick } from 'lucide-react'
import { useState } from 'react'
import { architectures } from '../../data/architectures'
import { ArchitectureDiagram, LaneLegend } from '../diagrams/ArchitectureDiagram'
import { laneLabel } from '../diagrams/lanes'
import { Reveal } from '../ui/Reveal'
import { Section } from '../ui/Section'

export function ArchitectureShowcase() {
  const [activeId, setActiveId] = useState(architectures[0].id)
  const arch = architectures.find((a) => a.id === activeId) ?? architectures[0]
  const [selected, setSelected] = useState<string | null>(arch.nodes[0].id)
  const node = arch.nodes.find((n) => n.id === selected) ?? null

  const switchTo = (id: string) => {
    setActiveId(id)
    const next = architectures.find((a) => a.id === id)
    setSelected(next?.nodes[0].id ?? null)
  }

  return (
    <Section
      id="architecture"
      eyebrow="04 · Architecture"
      title="How I approach AI engineering."
      intro="Three reference architectures behind my work. Select a component to see the design decision behind it."
    >
      <Reveal>
        <div role="tablist" aria-label="Architectures" className="mb-6 inline-flex flex-wrap gap-1 rounded-xl border border-line bg-surface p-1">
          {architectures.map((a) => (
            <button
              key={a.id}
              role="tab"
              type="button"
              id={`tab-${a.id}`}
              aria-selected={a.id === activeId}
              aria-controls={`panel-${a.id}`}
              onClick={() => switchTo(a.id)}
              className={`rounded-lg px-4 py-2 text-sm transition-colors ${
                a.id === activeId ? 'bg-surface-strong text-fg shadow-sm ring-1 ring-line-strong' : 'text-muted hover:text-fg'
              }`}
            >
              {a.name}
            </button>
          ))}
        </div>

        <div id={`panel-${arch.id}`} role="tabpanel" aria-labelledby={`tab-${arch.id}`} className="card overflow-hidden">
          <div className="relative border-b border-line px-4 py-8 sm:px-8">
            <div className="grid-bg pointer-events-none absolute inset-0" aria-hidden="true" />
            <AnimatePresence mode="wait">
              <motion.div
                className="relative"
                key={arch.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <ArchitectureDiagram arch={arch} selected={selected} onSelect={setSelected} />
              </motion.div>
            </AnimatePresence>
            <div className="relative mt-6 flex flex-wrap items-center justify-between gap-3">
              <LaneLegend />
              <span className="inline-flex items-center gap-1.5 text-xs text-subtle">
                <MousePointerClick size={13} aria-hidden="true" /> Select a component
              </span>
            </div>
          </div>

          <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1.2fr_1fr]">
            <div aria-live="polite">
              {node && (
                <>
                  <p className="font-mono text-[11px] tracking-[0.16em] text-subtle uppercase">{laneLabel[node.lane]}</p>
                  <h3 className="mt-2 text-lg font-semibold text-fg">
                    {node.label}
                    {node.sub && <span className="ml-2 font-mono text-xs font-normal text-subtle">{node.sub}</span>}
                  </h3>
                  <p className="mt-2 leading-relaxed text-muted">{node.detail}</p>
                </>
              )}
              <p className="mt-6 border-t border-line pt-5 text-sm leading-relaxed text-muted">{arch.summary}</p>
            </div>
            <div>
              <p className="font-mono text-[11px] tracking-[0.16em] text-subtle uppercase">Design principles</p>
              <ul className="mt-3 space-y-3">
                {arch.principles.map((p) => (
                  <li key={p} className="flex gap-3 text-sm leading-relaxed text-fg/90">
                    <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" aria-hidden="true" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </Reveal>
    </Section>
  )
}
