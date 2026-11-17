import { ChatWidget } from './components/chat/ChatWidget'
import { Footer } from './components/layout/Footer'
import { Navbar } from './components/layout/Navbar'
import { About } from './components/sections/About'
import { ArchitectureShowcase } from './components/sections/ArchitectureShowcase'
import { Contact } from './components/sections/Contact'
import { Education } from './components/sections/Education'
import { Experience } from './components/sections/Experience'
import { Expertise } from './components/sections/Expertise'
import { Hero } from './components/sections/Hero'
import { Projects } from './components/sections/Projects'

export default function App() {
  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[60] focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>
      <Navbar />
      <main id="main">
        <Hero />
        <About />
        <Expertise />
        <Projects />
        <ArchitectureShowcase />
        <Experience />
        <Education />
        <Contact />
      </main>
      <Footer />
      <ChatWidget />
    </>
  )
}
