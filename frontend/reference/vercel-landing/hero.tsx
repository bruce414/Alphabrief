import Link from "next/link"
import { Button } from "@/components/ui/button"
import { GradientText } from "@/components/ui/gradient-text"
import { ArrowRight, Play } from "lucide-react"

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 py-24 md:py-32">
      {/* Subtle gradient background */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-violet-100/40 via-transparent to-transparent" />
      
      <div className="mx-auto max-w-4xl text-center">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm">
          <span className="flex h-2 w-2 rounded-full bg-green-500" />
          <span className="text-muted-foreground">Now with multi-source analysis</span>
        </div>

        <h1 className="mb-6 text-4xl font-bold tracking-tight text-balance md:text-6xl lg:text-7xl">
          The platform for{" "}
          <GradientText>market research</GradientText>
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-lg text-muted-foreground text-balance md:text-xl">
          Input any source - text, URLs, or files - and let our AI deliver comprehensive 
          market analysis, competitor insights, and actionable trends in minutes.
        </p>

        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button size="lg" className="rounded-full px-8" asChild>
            <Link href="/auth/sign-up">
              Start free trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-full px-8" asChild>
            <Link href="#">
              <Play className="mr-2 h-4 w-4" />
              Watch demo
            </Link>
          </Button>
        </div>
      </div>
    </section>
  )
}
