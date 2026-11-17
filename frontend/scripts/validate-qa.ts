// Runs before every build (`npm run build`). Fails the build on a malformed Q&A file.
// Executed directly by Node (built-in TypeScript type stripping), no extra tooling.
import { readFileSync } from 'node:fs'
import { navItems } from '../src/data/profile.ts'
import { validateQA } from '../src/qa/validate.ts'

const root = new URL('../src/data/', import.meta.url)
const qa = JSON.parse(readFileSync(new URL('qa.json', root), 'utf8'))
const evalFile = JSON.parse(readFileSync(new URL('qa-eval.json', root), 'utf8'))
const sections = new Set<string>([...navItems.map((n) => n.id), 'top'])

const { errors, warnings, published } = validateQA(qa, sections, evalFile.cases ?? [])
for (const w of warnings) console.warn(`qa: warning  ${w}`)
for (const e of errors) console.error(`qa: ERROR    ${e}`)
if (errors.length) {
  console.error(`qa: ${errors.length} error(s) — fix src/data/qa.json (or run the generator's \`validate\`).`)
  process.exit(1)
}
console.log(`qa: ok — ${qa.items.length} items, ${published} published`)
