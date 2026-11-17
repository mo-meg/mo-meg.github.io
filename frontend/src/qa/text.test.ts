import { describe, expect, it } from 'vitest'
import { detectLang, tokenize } from './text'

describe('detectLang', () => {
  it('detects Arabic by script', () => {
    expect(detectLang('ما هي خبرة محمد في RAG؟')).toBe('ar')
  })
  it('detects German by function words and umlauts', () => {
    expect(detectLang('Welche Erfahrung hat er mit der Cloud?')).toBe('de')
    expect(detectLang('Wo wohnt er?')).toBe('de')
    expect(detectLang('Gehaltsvorstellung für München')).toBe('de')
  })
  it('detects English', () => {
    expect(detectLang('What is his experience with the cloud?')).toBe('en')
  })
  it('falls back to the UI language when there is no signal', () => {
    expect(detectLang('Prolumios', 'de')).toBe('de')
    expect(detectLang('pgvector', 'en')).toBe('en')
    expect(detectLang('', 'ar')).toBe('ar')
  })
})

describe('tokenize', () => {
  it('removes stop words, keeps names and technical terms', () => {
    expect(tokenize('What does Mohamed know about FastAPI and pgvector?', 'en')).toEqual(['mohamed', 'fastapi', 'pgvector'])
  })
  it('stems English plurals and gerunds lightly', () => {
    expect(tokenize('projects', 'en')).toEqual(['project'])
    expect(tokenize('monitoring', 'en')).toEqual(['monitor'])
  })
  it('folds German umlauts and stems', () => {
    expect(tokenize('Kenntnisse über Datenbanken', 'de')).toEqual(['kenntniss', 'datenbank'])
  })
  it('normalizes Arabic letter variants and strips the article', () => {
    const a = tokenize('الخبرة', 'ar')
    const b = tokenize('خبره', 'ar')
    expect(a).toEqual(b)
    expect(tokenize('ما هي إجابة محمد؟', 'ar')).toEqual(tokenize('ما هي اجابه محمد', 'ar'))
  })
})
