import { Capabilities } from '@/components/landing/capabilities'
import { CtaSection } from '@/components/landing/cta-section'
import { Hero } from '@/components/landing/hero'
import { MetricsMarquee } from '@/components/landing/metrics-marquee'
import { Pricing } from '@/components/landing/pricing'
import { Process } from '@/components/landing/process'
import { SiteFooter } from '@/components/layout/site-footer'
import { SiteNav } from '@/components/layout/site-nav'

export function LandingPage() {
  return (
    <div className="min-h-svh bg-background">
      <SiteNav variant="landing" />
      <main className="overflow-x-hidden">
        <Hero />
        <MetricsMarquee />
        <Capabilities />
        <Process />
        <Pricing />
        <CtaSection />
      </main>
      <SiteFooter />
    </div>
  )
}
