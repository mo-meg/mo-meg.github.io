import type { Lang } from './types'

/**
 * Text processing for the in-browser matcher: language detection, normalization,
 * stop-word removal, and deliberately light stemming for English, German, and Arabic.
 */

const ARABIC_CHAR = /[\u0600-\u06FF]/g
const ARABIC_DIACRITICS = /[\u064B-\u065F\u0670\u0640]/g

const STOP: Record<Lang, Set<string>> = {
  en: new Set(
    `a an the and or but of to in on at for from by with about as into than then so is are was were be been being am
    do does did done have has had can could would should will shall may might must i me my you your yo he him his she her
    it its we our they them their this that these those there here what which who whom whose when where why how
    tell say show explain describe give know let please any some more most much many very also just only not no yes
    use used uses using don doesn didn isn aren wasn won`
      .split(/\s+/)
      .filter(Boolean),
  ),
  de: new Set(
    `der die das den dem des ein eine einen einem einer eines und oder aber von zu im in an am auf fur fuer mit uber ueber
    als bei aus nach vor ist sind war waren sein seine seinen seinem seiner ihr ihre er sie es wir ich mich mir du dich
    dir hat haben hatte kann konnen koennen konnte wird werden wurde was welche welcher welches wer wen wem wie wo warum
    wann gibt es bitte erzahl erzaehl erzahle erzaehle sag sage zeig nenn mal doch noch auch nur nicht kein keine ja
    eigentlich denn genau`
      .split(/\s+/)
      .filter(Boolean),
  ),
  ar: new Set(
    `في من على الى عن مع هل ما ماذا من هو هي هم كيف لماذا متى اين اي التي الذي الذين هذا هذه ذلك تلك كان كانت يكون
    لدي لديه لديها له لها عند عنده ان او و ثم قد لقد كل بعض اخبرني اخبرنا حدثني اشرح وضح اعطني اريد ممكن يمكن
    السيد`
      .split(/\s+/)
      .filter(Boolean)
      .map((w) => normalizeArabic(w)),
  ),
}

/** Proper names and product names that must never be stemmed. */
const NO_STEM = new Set(['mohamed', 'mohammed', 'megahed', 'prolumios', 'moodle', 'medentity', 'ragas', 'aws', 'gcp'])

const DE_HINTS = /[äöüß]/i

function normalizeArabic(s: string): string {
  return s
    .replace(ARABIC_DIACRITICS, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/ؤ/g, 'و')
    .replace(/ئ/g, 'ي')
}

function foldLatin(s: string): string {
  return s
    .replace(/ß/g, 'ss')
    .normalize('NFD')
    .replace(/[\u0300-\u036F]/g, '')
}

/** Detects en / de / ar. `fallback` is used when the text gives no signal (e.g. a single product name). */
export function detectLang(text: string, fallback: Lang = 'en'): Lang {
  const letters = text.replace(/[^\p{L}]/gu, '')
  if (!letters) return fallback
  const arabic = (text.match(ARABIC_CHAR) ?? []).length
  if (arabic / letters.length > 0.3) return 'ar'
  const words = foldLatin(text.toLowerCase()).match(/\p{L}+/gu) ?? []
  let de = DE_HINTS.test(text) ? 2 : 0
  let en = 0
  for (const w of words) {
    if (STOP.de.has(w) && !STOP.en.has(w)) de++
    if (STOP.en.has(w) && !STOP.de.has(w)) en++
  }
  if (de > en) return 'de'
  if (en > de) return 'en'
  return fallback === 'ar' ? 'en' : fallback
}

function stemEn(t: string): string {
  if (t.length <= 4) return t
  if (t.endsWith('ies')) return t.slice(0, -3) + 'y'
  for (const suf of ['ing', 'ed', 'es', 's']) {
    if (t.endsWith(suf) && t.length - suf.length >= 4) return t.slice(0, -suf.length)
  }
  return t
}

function stemDe(t: string): string {
  if (t.length <= 5) return t
  for (const suf of ['ungen', 'en', 'er', 'es', 'em', 'e', 'n', 's']) {
    if (t.endsWith(suf) && t.length - suf.length >= 4) return t.slice(0, -suf.length)
  }
  return t
}

function stemAr(t: string): string {
  let s = t
  for (const pre of ['وال', 'بال', 'كال', 'فال', 'لل', 'ال']) {
    if (s.startsWith(pre) && s.length - pre.length >= 3) {
      s = s.slice(pre.length)
      break
    }
  }
  if (s.length > 4 && s.startsWith('و')) s = s.slice(1)
  for (const suf of ['ات', 'ون', 'ين', 'ها', 'ه', 'ي']) {
    if (s.endsWith(suf) && s.length - suf.length >= 3) return s.slice(0, -suf.length)
  }
  return s
}

/** Normalized, stop-word-free, stemmed content tokens. Latin tokens are stemmed with both stemmers' rules
 *  of the given language; technical terms (FastAPI, pgvector) survive unchanged in every language. */
export function tokenize(text: string, lang: Lang): string[] {
  const base = lang === 'ar' ? normalizeArabic(text.toLowerCase()) : text.toLowerCase()
  const raw = foldLatin(base).match(/[\p{L}\p{N}]+/gu) ?? []
  const out: string[] = []
  for (const tok of raw) {
    const isArabic = /[\u0600-\u06FF]/.test(tok)
    const t = isArabic ? normalizeArabic(tok) : tok
    if (t.length < 2 && !/\d/.test(t)) continue
    if (STOP.en.has(t) || STOP.de.has(t) || STOP.ar.has(t)) continue
    if (isArabic) {
      const s = stemAr(t)
      if (!STOP.ar.has(s)) out.push(s)
    } else {
      out.push(NO_STEM.has(t) ? t : lang === 'de' ? stemDe(t) : stemEn(t))
    }
  }
  return out
}
