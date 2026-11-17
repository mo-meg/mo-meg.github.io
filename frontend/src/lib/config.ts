declare const __HAS_CV__: boolean
declare const __QA_COUNT__: number

const base = import.meta.env.BASE_URL

/** Absolute-to-site path that respects the Vite base (GitHub Pages sub-path). */
export const asset = (path: string) => `${base}${path.replace(/^\//, '')}`

export const config = {
  /** Number of published Q&A items; the assistant is hidden when there are none. */
  qaCount: __QA_COUNT__,
  cvUrl: __HAS_CV__ ? asset('cv/Mohamed_Megahed_CV.pdf') : null,
}
