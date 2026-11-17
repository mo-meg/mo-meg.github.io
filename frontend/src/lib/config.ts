declare const __HAS_CV__: boolean

const base = import.meta.env.BASE_URL

/** Absolute-to-site path that respects the Vite base (GitHub Pages sub-path). */
export const asset = (path: string) => `${base}${path.replace(/^\//, '')}`

export const config = {
  /** Backend URL of the RAG assistant. When empty, the chat widget is not rendered. */
  chatApiUrl: ((import.meta.env.VITE_CHAT_API_URL as string | undefined) ?? '').replace(/\/$/, ''),
  cvUrl: __HAS_CV__ ? asset('cv/Mohamed_Megahed_CV.pdf') : null,
}
