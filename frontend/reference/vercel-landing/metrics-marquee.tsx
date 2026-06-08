"use client"

const metrics = [
  { value: "10x", label: "Faster research" },
  { value: "500+", label: "Reports generated" },
  { value: "95%", label: "Accuracy rate" },
  { value: "50k+", label: "Sources analyzed" },
  { value: "24/7", label: "AI availability" },
  { value: "3min", label: "Average time" },
]

export function MetricsMarquee() {
  return (
    <section className="border-y border-border bg-muted/30 py-8">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex items-center justify-center gap-12 overflow-hidden md:gap-16">
          {metrics.map((metric, index) => (
            <div key={index} className="flex flex-shrink-0 items-baseline gap-2">
              <span className="text-2xl font-bold tracking-tight md:text-3xl">{metric.value}</span>
              <span className="text-sm text-muted-foreground">{metric.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
