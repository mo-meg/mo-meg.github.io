export type Lang = 'en' | 'de' | 'ar'
export const LANGS: Lang[] = ['en', 'de', 'ar']

export type Category = 'profile' | 'experience' | 'projects' | 'skills' | 'cloud' | 'education' | 'contact'
export const CATEGORIES: Category[] = ['profile', 'experience', 'projects', 'skills', 'cloud', 'education', 'contact']

export type Status = 'draft' | 'approved' | 'needs-review'

export interface Localized {
  question: string
  answer: string
  paraphrases: string[]
}

export interface QASource {
  label: string
  href: string
}

/** Shape of an item as stored in src/data/qa.json. */
export interface QAItem {
  id: string
  category: Category
  status: Status
  sources: QASource[]
  related: string[]
  source_files?: Record<string, string>
  generated_hash?: string | null
  i18n: Record<Lang, Localized>
}

/** What the browser receives (via `virtual:qa`): no generator bookkeeping. */
export type PublishedItem = Omit<QAItem, 'source_files' | 'generated_hash'>

export interface EvalCase {
  text: string
  lang: Lang
  expected: string | null
}
