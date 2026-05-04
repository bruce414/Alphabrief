import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function CtaSection() {
  return (
    <section className="border-t border-border bg-muted/30 px-6 py-24 md:py-32">
      <div className="mx-auto max-w-3xl text-center">
        <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
          Ready to transform your research?
        </h2>
        <p className="mb-8 text-lg text-muted-foreground">
          Join thousands of researchers, analysts, and teams who save hours every week with AI-powered market intelligence.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button size="lg" className="rounded-full px-8" asChild>
            <Link href="/auth/sign-up">
              Start free trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button variant="outline" size="lg" className="rounded-full px-8" asChild>
            <Link href="#">Talk to sales</Link>
          </Button>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          No credit card required. Start with 5 free researches.
        </p>
      </div>
    </section>
  )
}
