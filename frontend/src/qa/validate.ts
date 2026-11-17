import type { EvalCase, QAItem } from './types.ts'

/** Build gate for src/data/qa.json. Shared by `scripts/validate-qa.ts` (prebuild) and the unit tests. */

const LANG_KEYS = ['en', 'de', 'ar'] as const
const CATEGORY_KEYS = ['profile', 'experience', 'projects', 'skills', 'cloud', 'education', 'contact']
const STATUSES = ['draft', 'approved', 'needs-review']
const ARABIC = /[؀-ۿ]/

export interface ValidationResult {
  errors: string[]
  warnings: string[]
  published: number
}

export function validateQA(
  data: { items?: QAItem[] },
  sections: Set<string>,
  evalCases: EvalCase[] = [],
): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []
  const items = Array.isArray(data.items) ? data.items : []
  if (!Array.isArray(data.items)) errors.push('qa.json: "items" must be an array')

  const ids = new Set<string>()
  for (const it of items) {
    const p = `[${it.id ?? '?'}]`
    if (!it.id || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(it.id)) errors.push(`${p} invalid id`)
    if (ids.has(it.id)) errors.push(`${p} duplicate id`)
    ids.add(it.id)
    if (!STATUSES.includes(it.status)) errors.push(`${p} invalid status "${it.status}"`)
    if (!CATEGORY_KEYS.includes(it.category)) errors.push(`${p} invalid category "${it.category}"`)
    for (const lang of LANG_KEYS) {
      const loc = it.i18n?.[lang]
      if (!loc) {
        errors.push(`${p} missing "${lang}" translation`)
        continue
      }
      if (!loc.question?.trim()) errors.push(`${p} empty ${lang} question`)
      if (!loc.answer?.trim()) errors.push(`${p} empty ${lang} answer`)
      const n = (loc.paraphrases ?? []).filter((x) => x.trim()).length
      if (n < 5 || n > 10) errors.push(`${p} ${lang} has ${n} paraphrases (expected 5–10)`)
      if (lang === 'ar' && !ARABIC.test(loc.question + loc.answer)) errors.push(`${p} "ar" text is not Arabic`)
    }
    for (const s of it.sources ?? []) {
      if (s.href.startsWith('#')) {
        if (!sections.has(s.href.slice(1))) errors.push(`${p} source link ${s.href} is not a page section`)
      } else if (!/^https:\/\/\S+$/.test(s.href)) {
        errors.push(`${p} source link must be https:// or #section: ${s.href}`)
      }
    }
  }
  for (const it of items) {
    for (const r of it.related ?? []) if (!ids.has(r)) errors.push(`[${it.id}] related id "${r}" does not exist`)
  }
  for (const c of evalCases) {
    if (c.expected && !ids.has(c.expected)) errors.push(`eval case "${c.text}" expects unknown id "${c.expected}"`)
  }

  const published = items.filter((i) => i.status === 'approved').length
  if (published === 0) warnings.push('no approved items — the assistant will be hidden on the published site')
  const pending = items.filter((i) => i.status !== 'approved').length
  if (pending) warnings.push(`${pending} item(s) not approved yet (draft / needs-review) — they are not published`)
  return { errors, warnings, published }
}
