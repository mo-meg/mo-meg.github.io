declare module 'virtual:qa' {
  import type { PublishedItem } from './types'
  /** Items published in this build: approved only (plus drafts when QA_INCLUDE_DRAFTS is on). */
  const items: PublishedItem[]
  export default items
  export const includesDrafts: boolean
}
