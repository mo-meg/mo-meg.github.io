/// <reference types="vitest/config" />
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv, type Plugin } from 'vite'

const QA_FILE = resolve(import.meta.dirname, 'src/data/qa.json')

/**
 * `virtual:qa` — the Q&A items that may be published. Unapproved items are filtered out at build
 * time, so drafts never reach the production bundle. Generator bookkeeping fields are stripped.
 */
function qaData(includeDrafts: boolean): Plugin {
  const id = 'virtual:qa'
  const resolved = '\0virtual:qa'
  return {
    name: 'portfolio-qa-data',
    resolveId(source) {
      return source === id ? resolved : undefined
    },
    load(source) {
      if (source !== resolved) return undefined
      this.addWatchFile(QA_FILE)
      const data = JSON.parse(readFileSync(QA_FILE, 'utf8')) as { items: Record<string, unknown>[] }
      const items = data.items
        .filter((it) => includeDrafts || it.status === 'approved')
        .map(({ source_files: _f, generated_hash: _h, ...rest }) => rest)
      return `export default ${JSON.stringify(items)};\nexport const includesDrafts = ${includeDrafts};\n`
    },
  }
}

// Base path:
//  - "/"              for a user site (mmm-megahed.github.io) or a custom domain
//  - "/<repo-name>/"  for a project site (mmm-megahed.github.io/<repo-name>/)
// The GitHub Actions workflow computes this automatically and passes VITE_BASE_PATH.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  let base = env.VITE_BASE_PATH || '/'
  if (!base.startsWith('/')) base = `/${base}`
  if (!base.endsWith('/')) base = `${base}/`

  // Drafts are visible in `npm run dev` (with a badge) unless QA_INCLUDE_DRAFTS=false;
  // production builds publish approved items only unless QA_INCLUDE_DRAFTS=true is set explicitly.
  const includeDrafts = env.QA_INCLUDE_DRAFTS ? env.QA_INCLUDE_DRAFTS === 'true' : mode === 'development'

  const qaCount = (JSON.parse(readFileSync(QA_FILE, 'utf8')).items as { status: string }[]).filter(
    (it) => includeDrafts || it.status === 'approved',
  ).length

  // The "Download CV" button is only rendered when the PDF actually exists,
  // so the published site never contains a broken download link.
  const hasCv = existsSync(resolve(import.meta.dirname, 'public/cv/Mohamed_Megahed_CV.pdf'))

  return {
    base,
    plugins: [react(), tailwindcss(), qaData(includeDrafts)],
    define: {
      __HAS_CV__: JSON.stringify(hasCv),
      // Lets the page decide whether to show the assistant without bundling the Q&A data eagerly.
      __QA_COUNT__: JSON.stringify(qaCount),
    },
    build: {
      target: 'es2022',
      sourcemap: false,
    },
    test: {
      include: ['src/**/*.test.ts'],
      environment: 'node',
    },
  }
})
