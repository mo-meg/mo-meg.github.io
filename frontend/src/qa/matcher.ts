import { detectLang, tokenize } from './text'
import type { Lang, PublishedItem } from './types'
import { LANGS } from './types'

/**
 * In-browser question matcher.
 *
 * Every prepared question and its paraphrases (in all three languages) is a "variant".
 * A visitor query is scored against each variant:
 *   score = 0.75 · (IDF-weighted share of the query's terms found in the variant)
 *         + 0.25 · (IDF-weighted share of the variant's terms found in the query)
 * Exact token matches count 1, fuzzy matches (prefix / one edit) count 0.8.
 * Terms never seen in the Q&A get the maximum IDF, so off-topic words pull the score down.
 * The best variant per item is the item's score; below `threshold` the assistant falls back to "contact me".
 */

/** Chosen with the threshold sweep in matcher.test.ts (qa-eval.json). Re-check after large Q&A changes. */
export const DEFAULT_THRESHOLD = 0.4

interface Variant {
  itemId: string
  tokens: string[]
}

export interface Match {
  item: PublishedItem
  score: number
}

export interface MatchResult {
  lang: Lang
  best: Match | null // null → fall back to contact
  suggestions: PublishedItem[] // "did you mean" (closest items, even below the threshold)
}

function editDistanceAtMostOne(a: string, b: string): boolean {
  if (Math.abs(a.length - b.length) > 1) return false
  let i = 0
  let j = 0
  let edits = 0
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      i++
      j++
      continue
    }
    if (++edits > 1) return false
    if (a.length > b.length) i++
    else if (b.length > a.length) j++
    else {
      i++
      j++
    }
  }
  return edits + (a.length - i) + (b.length - j) <= 1
}

function tokenSimilarity(q: string, v: string): number {
  if (q === v) return 1
  const short = q.length < v.length ? q : v
  const long = q.length < v.length ? v : q
  if (short.length >= 4 && long.startsWith(short)) return 0.8
  if (short.length >= 5 && editDistanceAtMostOne(q, v)) return 0.8
  return 0
}

export class Matcher {
  private variants: Variant[] = []
  private idf = new Map<string, number>()
  private maxIdf = 1
  private byId = new Map<string, PublishedItem>()
  readonly threshold: number

  constructor(items: PublishedItem[], threshold = DEFAULT_THRESHOLD) {
    this.threshold = threshold
    const docFreq = new Map<string, number>()
    for (const item of items) {
      this.byId.set(item.id, item)
      const itemTerms = new Set<string>()
      for (const lang of LANGS) {
        const loc = item.i18n[lang]
        if (!loc) continue
        for (const text of [loc.question, ...loc.paraphrases]) {
          const tokens = [...new Set(tokenize(text, lang))]
          if (!tokens.length) continue
          this.variants.push({ itemId: item.id, tokens })
          tokens.forEach((t) => itemTerms.add(t))
        }
      }
      itemTerms.forEach((t) => docFreq.set(t, (docFreq.get(t) ?? 0) + 1))
    }
    const n = Math.max(items.length, 1)
    for (const [t, df] of docFreq) this.idf.set(t, Math.log(1 + n / df))
    this.maxIdf = Math.log(1 + n)
  }

  private weight(t: string) {
    return this.idf.get(t) ?? this.maxIdf
  }

  private scoreVariant(query: string[], v: Variant): number {
    let qTotal = 0
    let qHit = 0
    const vMatched = new Map<string, number>()
    for (const q of query) {
      const w = this.weight(q)
      qTotal += w
      let best = 0
      let bestTok = ''
      for (const t of v.tokens) {
        const s = tokenSimilarity(q, t)
        if (s > best) {
          best = s
          bestTok = t
        }
        if (best === 1) break
      }
      if (best > 0) {
        qHit += w * best
        vMatched.set(bestTok, Math.max(vMatched.get(bestTok) ?? 0, best))
      }
    }
    if (!qTotal || !qHit) return 0
    let vTotal = 0
    let vHit = 0
    for (const t of v.tokens) {
      const w = this.weight(t)
      vTotal += w
      vHit += w * (vMatched.get(t) ?? 0)
    }
    return 0.75 * (qHit / qTotal) + 0.25 * (vTotal ? vHit / vTotal : 0)
  }

  /** All items ranked by their best-variant score for the query. */
  rank(query: string, lang: Lang): Match[] {
    const tokens = [...new Set(tokenize(query, lang))]
    if (!tokens.length) return []
    const best = new Map<string, number>()
    for (const v of this.variants) {
      const s = this.scoreVariant(tokens, v)
      if (s > (best.get(v.itemId) ?? 0)) best.set(v.itemId, s)
    }
    return [...best.entries()]
      .map(([id, score]) => ({ item: this.byId.get(id)!, score }))
      .sort((a, b) => b.score - a.score)
  }

  match(query: string, uiLang: Lang = 'en'): MatchResult {
    const lang = detectLang(query, uiLang)
    const ranked = this.rank(query, lang)
    const top = ranked[0]
    const best = top && top.score >= this.threshold ? top : null
    const suggestions = ranked
      .filter((m) => m !== best && m.score >= this.threshold * 0.4)
      .slice(0, 3)
      .map((m) => m.item)
    return { lang, best, suggestions }
  }

  get(id: string) {
    return this.byId.get(id)
  }
}
