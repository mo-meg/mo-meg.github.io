import { describe, expect, it } from 'vitest'
import qaData from '../data/qa.json'
import evalData from '../data/qa-eval.json'
import { navItems } from '../data/profile'
import { DEFAULT_THRESHOLD, Matcher } from './matcher'
import type { EvalCase, PublishedItem, QAItem } from './types'
import { validateQA } from './validate'

// The threshold test runs against ALL items (drafts included), so it stays meaningful before approval.
const items = qaData.items as unknown as QAItem[]
const cases = evalData.cases as EvalCase[]

function mk(id: string, en: string, de: string, ar: string, paraphrases: string[] = []): PublishedItem {
  const loc = (q: string) => ({ question: q, answer: `answer ${id}`, paraphrases })
  return { id, category: 'profile', status: 'approved', sources: [], related: [], i18n: { en: loc(en), de: loc(de), ar: loc(ar) } }
}

describe('Matcher (unit)', () => {
  const m = new Matcher([
    mk('contact', 'How can I contact Mohamed?', 'Wie kann ich Mohamed kontaktieren?', 'كيف أتواصل مع محمد؟', ['email address']),
    mk('rag', 'What experience does he have with RAG?', 'Welche Erfahrung hat er mit RAG?', 'ما خبرته في RAG؟', ['retrieval augmented generation']),
  ])

  it('matches exact and reworded questions', () => {
    expect(m.match('How can I contact Mohamed?').best?.item.id).toBe('contact')
    expect(m.match("what's his email address").best?.item.id).toBe('contact')
    expect(m.match('retrieval augmented generation experience').best?.item.id).toBe('rag')
  })

  it('tolerates typos and inflections', () => {
    expect(m.match('retreival augmented generations').best?.item.id).toBe('rag')
  })

  it('answers in the language of the question', () => {
    expect(m.match('Wie kann ich ihn kontaktieren?').lang).toBe('de')
    expect(m.match('كيف أتواصل معه؟').lang).toBe('ar')
  })

  it('falls back for unrelated questions and empty input', () => {
    expect(m.match('best pizza in town').best).toBeNull()
    expect(m.match('hello').best).toBeNull()
    expect(m.match('???').best).toBeNull()
  })
})

describe('qa.json', () => {
  it('passes the build validation', () => {
    const sections = new Set<string>([...navItems.map((n) => n.id), 'top'])
    const { errors } = validateQA({ items }, sections, cases)
    expect(errors).toEqual([])
  })
})

describe('threshold on the evaluation set (qa-eval.json)', () => {
  const matcher = new Matcher(items as PublishedItem[])
  const positives = cases.filter((c) => c.expected)
  const negatives = cases.filter((c) => !c.expected)

  function measure(threshold: number) {
    let tp = 0
    let tn = 0
    const misses: string[] = []
    for (const c of positives) {
      const top = matcher.rank(c.text, c.lang)[0]
      if (top && top.score >= threshold && top.item.id === c.expected) tp++
      else misses.push(`${c.text} → ${top?.item.id ?? '∅'} (${top?.score.toFixed(2) ?? 0})`)
    }
    for (const c of negatives) {
      const top = matcher.rank(c.text, c.lang)[0]
      if (!top || top.score < threshold) tn++
      else misses.push(`NEG ${c.text} → ${top.item.id} (${top.score.toFixed(2)})`)
    }
    return { recall: tp / positives.length, rejection: tn / negatives.length, misses }
  }

  it('has enough cases', () => {
    expect(positives.length).toBeGreaterThanOrEqual(40)
    expect(negatives.length).toBeGreaterThanOrEqual(30)
  })

  it(`DEFAULT_THRESHOLD (${DEFAULT_THRESHOLD}) matches ≥90% of rewordings and rejects ≥95% of off-topic questions`, () => {
    const sweep = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7].map((t) => ({ t, ...measure(t) }))
    console.log(
      'threshold sweep (recall / rejection):\n' +
        sweep.map((s) => `  ${s.t.toFixed(2)}  ${(s.recall * 100).toFixed(0)}% / ${(s.rejection * 100).toFixed(0)}%`).join('\n'),
    )
    const r = measure(DEFAULT_THRESHOLD)
    if (r.misses.length) console.log('misses at default threshold:\n  ' + r.misses.join('\n  '))
    expect(r.recall).toBeGreaterThanOrEqual(0.9)
    expect(r.rejection).toBeGreaterThanOrEqual(0.95)
  })
})
