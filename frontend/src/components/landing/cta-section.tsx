import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function CtaSection() {
  return (
    <section
      id="cta"
      className="scroll-mt-20 border-t border-border bg-muted/30 px-6 py-24 md:py-32"
    >
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
          Follow the AlphaBrief preview
        </h2>
        <p className="mb-8 text-lg text-muted-foreground">
          We’re building in the open. Try the app shell, send feedback, and
          watch this space as milestones ship.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button size="lg" className="rounded-full px-8" asChild>
            <Link to="/register">
              Get started
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-full px-8" asChild>
            <a href="#features">Back to features</a>
          </Button>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Bookmark this page—the public preview will live here as we ship
          milestones.
        </p>
      </div>
    </section>
  )
}
