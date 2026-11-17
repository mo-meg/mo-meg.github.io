import { profile } from '../../data/profile'

const year = new Date().getFullYear()

export function Footer() {
  return (
    <footer className="border-t border-line py-8">
      <div className="container-page flex flex-col items-center justify-between gap-3 text-sm text-subtle sm:flex-row">
        <p>
          © {year} {profile.name} · {profile.location}
        </p>
        <p className="font-mono text-xs">Built with React, TypeScript & Tailwind · Deployed on GitHub Pages</p>
      </div>
    </footer>
  )
}
