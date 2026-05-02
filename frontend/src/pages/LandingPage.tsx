import { Capabilities } from '@/components/landing/capabilities'
import { CtaSection } from '@/components/landing/cta-section'
import { Hero } from '@/components/landing/hero'
import { MetricsMarquee } from '@/components/landing/metrics-marquee'
import { Pricing } from '@/components/landing/pricing'
import { Process } from '@/components/landing/process'
import { SiteFooter } from '@/components/landing/site-footer'
import { SiteHeader } from '@/components/landing/site-header'

export function LandingPage() {
  return (
    <div className="min-h-svh bg-background">
      <SiteHeader />
      <main>
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
