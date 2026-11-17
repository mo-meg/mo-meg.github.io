import { existsSync } from 'node:fs'
import { resolve } from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// Base path:
//  - "/"              for a user site (mmm-megahed.github.io) or a custom domain
//  - "/<repo-name>/"  for a project site (mmm-megahed.github.io/<repo-name>/)
// The GitHub Actions workflow computes this automatically and passes VITE_BASE_PATH.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  let base = env.VITE_BASE_PATH || '/'
  if (!base.startsWith('/')) base = `/${base}`
  if (!base.endsWith('/')) base = `${base}/`

  // The "Download CV" button is only rendered when the PDF actually exists,
  // so the published site never contains a broken download link.
  const hasCv = existsSync(resolve(import.meta.dirname, 'public/cv/Mohamed_Megahed_CV.pdf'))

  return {
    base,
    plugins: [react(), tailwindcss()],
    define: {
      __HAS_CV__: JSON.stringify(hasCv),
    },
    build: {
      target: 'es2022',
      sourcemap: false,
    },
  }
})
