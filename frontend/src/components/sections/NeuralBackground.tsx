import { useEffect, useRef } from 'react'

/**
 * Subtle animated embedding-space background: drifting nodes, connected when close,
 * with occasional "signal" pulses travelling along edges. Pauses when off-screen
 * or when the tab is hidden; renders a single static frame for reduced motion.
 */
export function NeuralBackground() {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let width = 0
    let height = 0
    let dpr = 1
    let raf = 0
    let visible = true

    type Node = { x: number; y: number; vx: number; vy: number; r: number; hub: boolean }
    type Pulse = { a: number; b: number; t: number; speed: number }
    let nodes: Node[] = []
    let pulses: Pulse[] = []

    const color = () => getComputedStyle(document.documentElement).getPropertyValue('--node').trim() || '34, 211, 238'
    let rgb = color()

    const init = () => {
      const rect = canvas.getBoundingClientRect()
      width = rect.width
      height = rect.height
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      const count = Math.round(Math.min(90, Math.max(28, (width * height) / 16000)))
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.18,
        vy: (Math.random() - 0.5) * 0.18,
        r: Math.random() * 1.3 + 0.6,
        hub: Math.random() < 0.08,
      }))
      pulses = []
    }

    const maxDist = () => Math.min(170, Math.max(110, width / 9))

    const draw = () => {
      ctx.clearRect(0, 0, width, height)
      const md = maxDist()
      const edges: [number, number][] = []

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]
          const b = nodes[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const d = Math.hypot(dx, dy)
          if (d < md) {
            edges.push([i, j])
            ctx.strokeStyle = `rgba(${rgb}, ${(1 - d / md) * 0.16})`
            ctx.lineWidth = 0.6
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.stroke()
          }
        }
      }

      for (const n of nodes) {
        ctx.fillStyle = `rgba(${rgb}, ${n.hub ? 0.85 : 0.45})`
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.hub ? n.r + 1.2 : n.r, 0, Math.PI * 2)
        ctx.fill()
      }

      // Signal pulses travelling along existing edges.
      if (!reduce && edges.length && pulses.length < 6 && Math.random() < 0.035) {
        const [a, b] = edges[Math.floor(Math.random() * edges.length)]
        pulses.push({ a, b, t: 0, speed: 0.008 + Math.random() * 0.01 })
      }
      pulses = pulses.filter((p) => p.t <= 1)
      for (const p of pulses) {
        const a = nodes[p.a]
        const b = nodes[p.b]
        const x = a.x + (b.x - a.x) * p.t
        const y = a.y + (b.y - a.y) * p.t
        const g = ctx.createRadialGradient(x, y, 0, x, y, 6)
        g.addColorStop(0, `rgba(${rgb}, 0.9)`)
        g.addColorStop(1, `rgba(${rgb}, 0)`)
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(x, y, 6, 0, Math.PI * 2)
        ctx.fill()
        p.t += p.speed
      }
    }

    const step = () => {
      for (const n of nodes) {
        n.x += n.vx
        n.y += n.vy
        if (n.x < -20) n.x = width + 20
        if (n.x > width + 20) n.x = -20
        if (n.y < -20) n.y = height + 20
        if (n.y > height + 20) n.y = -20
      }
      draw()
      raf = requestAnimationFrame(step)
    }

    const start = () => {
      cancelAnimationFrame(raf)
      if (reduce) draw()
      else if (visible && !document.hidden) raf = requestAnimationFrame(step)
    }

    init()
    start()

    const ro = new ResizeObserver(() => {
      init()
      start()
    })
    ro.observe(canvas)

    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting
      start()
    })
    io.observe(canvas)

    const onVis = () => (document.hidden ? cancelAnimationFrame(raf) : start())
    document.addEventListener('visibilitychange', onVis)

    // Re-read the accent colour when the theme class changes.
    const mo = new MutationObserver(() => {
      rgb = color()
      if (reduce) draw()
    })
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      io.disconnect()
      mo.disconnect()
      document.removeEventListener('visibilitychange', onVis)
    }
  }, [])

  return <canvas ref={ref} aria-hidden="true" className="absolute inset-0 h-full w-full" />
}
