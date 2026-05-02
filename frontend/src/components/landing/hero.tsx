import { ArrowRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { GradientText } from '@/components/ui/gradient-text'

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 py-24 md:py-32">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-200/50 via-transparent to-transparent dark:from-slate-800/40" />

      <div className="mx-auto max-w-4xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm">
          <span className="flex h-2 w-2 rounded-full bg-emerald-600/80" />
          <span className="text-muted-foreground">
            Early prototype · Multi-source input
          </span>
        </div>

        <h1 className="mb-6 text-balance text-4xl font-bold tracking-tight md:text-6xl lg:text-7xl">
          <span className="text-foreground">AI-powered financial briefings </span>
          <GradientText>for investors</GradientText>
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-balance text-lg text-muted-foreground md:text-xl">
          Turn scattered sources into clearer investment context—structured
          briefs and source-aware analysis, built for people who read filings,
          calls, and research daily.
        </p>

        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button size="lg" className="rounded-full px-8" asChild>
            <a href="#capabilities">
              See capabilities
              <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
          <Button variant="outline" size="lg" className="rounded-full px-8" asChild>
            <a href="#cta">Request early access</a>
          </Button>
        </div>
      </div>
    </section>
  )
}
