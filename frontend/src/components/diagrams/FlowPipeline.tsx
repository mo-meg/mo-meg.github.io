import { ChevronRight } from 'lucide-react'
import type { FlowStage } from '../../data/projects'

/** Compact linear workflow diagram used inside project case studies. */
export function FlowPipeline({ stages, label }: { stages: FlowStage[]; label: string }) {
  return (
    <ol className="flex flex-wrap items-stretch gap-y-2" aria-label={label}>
      {stages.map((s, i) => (
        <li key={s.label} className="flex items-center">
          <div className="rounded-lg border border-line bg-surface-strong px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-accent">{String(i + 1).padStart(2, '0')}</span>
              <span className="text-[13px] font-medium text-fg">{s.label}</span>
            </div>
            {s.detail && <div className="mt-0.5 pl-6 font-mono text-[10.5px] text-subtle">{s.detail}</div>}
          </div>
          {i < stages.length - 1 && <ChevronRight size={15} className="mx-1 shrink-0 text-subtle" aria-hidden="true" />}
        </li>
      ))}
    </ol>
  )
}
