import { BarChart3, FileText, Layers, Target } from 'lucide-react'

const capabilities = [
  {
    number: '01',
    title: 'Multi-source input',
    description:
      'Bring URLs, notes, and documents together. AlphaBrief is designed to synthesize context across the sources you already use.',
    icon: FileText,
  },
  {
    number: '02',
    title: 'Structured financial briefs',
    description:
      'Receive organized output—summaries, themes, and cited references—so you can scan decisions faster than raw pages alone.',
    icon: Layers,
  },
  {
    number: '03',
    title: 'Source-aware analysis',
    description:
      'Analysis that stays grounded in what you provided, with explicit sourcing so you can verify and drill down.',
    icon: BarChart3,
  },
  {
    number: '04',
    title: 'Built for investors',
    description:
      'Workflows and language tuned for equity research, portfolio context, and disciplined reading—not generic “insights.”',
    icon: Target,
  },
]

export function Capabilities() {
  return (
    <section id="capabilities" className="scroll-mt-20 px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 max-w-2xl">
          <p className="mb-3 text-sm font-medium text-primary">Capabilities</p>
          <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
            From scattered sources to clearer context
          </h2>
          <p className="text-lg text-muted-foreground">
            Honest, prototype-stage capability—focused on structure,
            sourcing, and investor-grade readability.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {capabilities.map((capability) => (
            <div
              key={capability.number}
              className="group relative rounded-2xl border border-border bg-card p-8 transition-all hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5"
            >
              <div className="mb-6 flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  {capability.number}
                </span>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted transition-colors group-hover:bg-primary/10">
                  <capability.icon className="h-5 w-5 text-muted-foreground transition-colors group-hover:text-primary" />
                </div>
              </div>
              <h3 className="mb-3 text-xl font-semibold">{capability.title}</h3>
              <p className="text-muted-foreground">{capability.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
