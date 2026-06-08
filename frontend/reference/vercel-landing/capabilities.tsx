import { FileText, Globe, BarChart3, Share2 } from "lucide-react"

const capabilities = [
  {
    number: "01",
    title: "Multi-source Input",
    description: "Input text, paste URLs, or upload documents. Our AI processes any format to extract valuable market intelligence.",
    icon: FileText,
  },
  {
    number: "02",
    title: "Deep AI Analysis",
    description: "Our agent researches across multiple sources, validates findings, and compiles comprehensive market insights.",
    icon: Globe,
  },
  {
    number: "03",
    title: "Structured Reports",
    description: "Get organized results with executive summaries, key insights, market trends, and competitor analysis.",
    icon: BarChart3,
  },
  {
    number: "04",
    title: "Export & Share",
    description: "Download reports as PDF, share with your team, or integrate with your workflow via our API.",
    icon: Share2,
  },
]

export function Capabilities() {
  return (
    <section id="features" className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 max-w-2xl">
          <p className="mb-3 text-sm font-medium text-primary">Capabilities</p>
          <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
            Everything you need. Nothing you don&apos;t.
          </h2>
          <p className="text-lg text-muted-foreground">
            From input to insight, every step is designed to deliver maximum value with minimum friction.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {capabilities.map((capability) => (
            <div 
              key={capability.number}
              className="group relative rounded-2xl border border-border bg-card p-8 transition-all hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5"
            >
              <div className="mb-6 flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">{capability.number}</span>
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
