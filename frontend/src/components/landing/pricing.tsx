import { Check } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const plans = [
  {
    name: 'Free',
    price: '$0',
    description: 'Explore the prototype during beta.',
    features: [
      'Access while the product is in early preview',
      'Core briefing workflow (limits may apply)',
      'Help shape the roadmap with feedback',
    ],
    cta: 'Join the waitlist',
    popular: false,
    href: '#cta',
  },
  {
    name: 'Pro',
    price: 'Planned',
    period: '',
    description: 'For professionals when paid plans launch—not billing yet.',
    features: [
      'Higher usage limits (details TBD)',
      'Priority guidance as features stabilize',
      'Workspace-oriented workflows (planned)',
      'API access under fair use (planned)',
    ],
    cta: 'Get notified',
    popular: true,
    href: '#cta',
  },
  {
    name: 'Student Pro',
    price: 'Planned',
    description: 'Discounted path for students—we are validating demand.',
    features: [
      'Education-verified pricing (coming later)',
      'Same core brief quality as Pro when available',
      'Lightweight billing—no enterprise baggage',
    ],
    cta: 'Tell us you’re interested',
    popular: false,
    href: '#cta',
  },
]

export function Pricing() {
  return (
    <section id="pricing" className="scroll-mt-20 px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-medium text-primary">Pricing</p>
          <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
            Beta-friendly, transparent plans
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            Today we’re focused on the prototype. Paid tiers are framed as
            planned—you won’t see surprise charges while we’re in preview.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={cn(
                'relative rounded-2xl border p-8 transition-all',
                plan.popular
                  ? 'border-primary bg-card shadow-lg shadow-primary/10'
                  : 'border-border bg-card hover:border-primary/20',
              )}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="rounded-full bg-primary px-3 py-1 text-xs font-medium text-primary-foreground">
                    Focus area
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="mb-2 text-xl font-semibold">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.period ? (
                    <span className="text-muted-foreground">{plan.period}</span>
                  ) : null}
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                  {plan.description}
                </p>
              </div>

              <ul className="mb-8 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-3 text-sm">
                    <Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                className={cn(
                  'w-full rounded-full',
                  plan.popular ? '' : 'bg-foreground hover:bg-foreground/90',
                )}
                variant={plan.popular ? 'default' : 'secondary'}
                asChild
              >
                <a href={plan.href}>{plan.cta}</a>
              </Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
