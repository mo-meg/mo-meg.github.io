import { ArrowDown } from 'lucide-react'
import type { KeyboardEvent } from 'react'
import type { ArchNode, Architecture, Lane } from '../../data/architectures'
import { laneColor, laneLabel } from './lanes'

const CELL_W = 184
const CELL_H = 112
const NODE_W = 152
const NODE_H = 64

const colsClass: Record<number, string> = { 1: '', 2: 'grid-cols-2', 3: 'grid-cols-3' }


interface Props {
  arch: Architecture
  selected: string | null
  onSelect: (id: string) => void
}

function box(n: ArchNode) {
  const [c, r] = n.pos
  const x = c * CELL_W + (CELL_W - NODE_W) / 2
  const y = r * CELL_H + (CELL_H - NODE_H) / 2
  return { x, y, cx: x + NODE_W / 2, cy: y + NODE_H / 2 }
}

function edgePath(a: ArchNode, b: ArchNode) {
  const A = box(a)
  const B = box(b)
  if (a.pos[0] === b.pos[0]) {
    // vertical
    const down = b.pos[1] > a.pos[1]
    return `M ${A.cx} ${down ? A.y + NODE_H : A.y} V ${down ? B.y : B.y + NODE_H}`
  }
  const right = b.pos[0] > a.pos[0]
  const sx = right ? A.x + NODE_W : A.x
  const tx = right ? B.x : B.x + NODE_W
  if (a.pos[1] === b.pos[1]) return `M ${sx} ${A.cy} H ${tx}`
  const mid = (sx + tx) / 2
  const r = 8
  const dir = B.cy > A.cy ? 1 : -1
  const h = right ? 1 : -1
  // Rounded elbow
  return `M ${sx} ${A.cy} H ${mid - r * h} Q ${mid} ${A.cy} ${mid} ${A.cy + r * dir} V ${B.cy - r * dir} Q ${mid} ${B.cy} ${mid + r * h} ${B.cy} H ${tx}`
}

function mobileGroups(arch: Architecture): ArchNode[][] {
  const connected = new Set(arch.edges.map(([a, b]) => `${a}>${b}`))
  const groups: ArchNode[][] = []
  for (const n of arch.nodes) {
    const last = groups[groups.length - 1]
    const prev = last?.[last.length - 1]
    if (prev && prev.pos[0] === n.pos[0] && !connected.has(`${prev.id}>${n.id}`) && !connected.has(`${n.id}>${prev.id}`)) {
      last.push(n)
    } else {
      groups.push([n])
    }
  }
  return groups
}

/** Engineering-style architecture diagram. SVG on wide screens, a vertical list on narrow ones. */
export function ArchitectureDiagram({ arch, selected, onSelect }: Props) {
  const cols = Math.max(...arch.nodes.map((n) => n.pos[0])) + 1
  const rows = Math.max(...arch.nodes.map((n) => n.pos[1])) + 1
  const W = cols * CELL_W
  const H = rows * CELL_H
  const byId = Object.fromEntries(arch.nodes.map((n) => [n.id, n]))
  const markerId = `arrow-${arch.id}`

  const onKey = (e: KeyboardEvent, id: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onSelect(id)
    }
  }

  return (
    <>
      {/* Desktop / tablet: SVG diagram */}
      <div className="hidden md:block">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="mx-auto h-auto w-full"
          style={{ maxWidth: W * 1.12 }}
          role="group"
          aria-label={`${arch.name} diagram`}
        >
          <defs>
            <marker id={markerId} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--fg-subtle)" />
            </marker>
          </defs>

          {arch.edges.map(([from, to]) => {
            const d = edgePath(byId[from], byId[to])
            const active = selected === from || selected === to
            return (
              <g key={`${from}-${to}`}>
                <path d={d} fill="none" stroke="var(--border-strong)" strokeWidth={1.25} markerEnd={`url(#${markerId})`} />
                <path
                  d={d}
                  fill="none"
                  stroke="var(--accent)"
                  strokeOpacity={active ? 0.95 : 0.45}
                  strokeWidth={active ? 1.8 : 1.25}
                  strokeDasharray="4 10"
                  className="arch-flow"
                />
              </g>
            )
          })}

          {arch.nodes.map((n) => {
            const { x, y } = box(n)
            const isSel = selected === n.id
            const color = laneColor[n.lane]
            return (
              <g
                key={n.id}
                role="button"
                tabIndex={0}
                aria-pressed={isSel}
                aria-label={`${n.label}${n.sub ? ` (${n.sub})` : ''}`}
                onClick={() => onSelect(n.id)}
                onKeyDown={(e) => onKey(e, n.id)}
                className="cursor-pointer outline-none [&:focus-visible>rect:first-of-type]:stroke-[var(--accent)]"
              >
                <rect
                  x={x}
                  y={y}
                  width={NODE_W}
                  height={NODE_H}
                  rx={10}
                  fill="var(--surface-strong)"
                  stroke={isSel ? color : 'var(--border-strong)'}
                  strokeWidth={isSel ? 1.6 : 1}
                  style={{ transition: 'stroke 200ms' }}
                />
                <rect x={x} y={y + 14} width={2.5} height={NODE_H - 28} rx={1.25} fill={color} />
                <text x={x + 14} y={y + 27} fill="var(--fg)" fontSize={12.5} fontWeight={600} fontFamily="var(--font-sans)">
                  {n.label}
                </text>
                {n.sub && (
                  <text x={x + 14} y={y + 45} fill="var(--fg-subtle)" fontSize={10} fontFamily="var(--font-mono)">
                    {n.sub}
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      {/* Mobile: vertical pipeline. Parallel inputs (same column, not connected) share a row. */}
      <ol className="space-y-1.5 md:hidden" aria-label={`${arch.name} pipeline`}>
        {mobileGroups(arch).map((group, i, all) => (
          <li key={group.map((n) => n.id).join('-')}>
            <div className={`grid gap-1.5 ${colsClass[Math.min(group.length, 3)]}`}>
              {group.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => onSelect(n.id)}
                  aria-pressed={selected === n.id}
                  className={`flex w-full items-center gap-3 rounded-xl border bg-surface-strong px-3 py-3 text-left transition-colors ${
                    selected === n.id ? 'border-accent/70' : 'border-line'
                  }`}
                >
                  <span className="h-8 w-[3px] shrink-0 rounded-full" style={{ background: laneColor[n.lane] }} aria-hidden="true" />
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold text-fg">{n.label}</span>
                    {n.sub && <span className="block truncate font-mono text-[11px] text-subtle">{n.sub}</span>}
                  </span>
                </button>
              ))}
            </div>
            {i < all.length - 1 && <ArrowDown size={14} className="mx-auto my-1 text-subtle" aria-hidden="true" />}
          </li>
        ))}
      </ol>
    </>
  )
}

export function LaneLegend() {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted">
      {(Object.keys(laneColor) as Lane[]).map((l) => (
        <li key={l} className="inline-flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: laneColor[l] }} aria-hidden="true" />
          {laneLabel[l]}
        </li>
      ))}
    </ul>
  )
}
