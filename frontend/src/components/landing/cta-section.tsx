import { ArrowRight } from 'lucide-react'

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
          We’re building in the open. Request early access for updates, beta
          invitations, and changelog-style progress—no hype, just the work.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button size="lg" className="rounded-full px-8" asChild>
            <a href="mailto:?subject=AlphaBrief%20early%20access&body=Please%20keep%20me%20posted%20on%20the%20prototype.">
              Request early access
              <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
          <Button variant="outline" size="lg" className="rounded-full px-8" asChild>
            <a href="#capabilities">Back to capabilities</a>
          </Button>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Prefer not to email? Bookmark this page—the public preview will live
          here as we ship milestones.
        </p>
      </div>
    </section>
  )
}
