const highlights = [
  'Multi-source input',
  'Structured financial briefs',
  'Source-aware analysis',
  'Built for investors',
  'Early prototype',
]

export function MetricsMarquee() {
  return (
    <section className="border-y border-border bg-muted/30 py-8">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 md:gap-x-14">
          {highlights.map((label) => (
            <span
              key={label}
              className="text-sm font-medium tracking-tight text-muted-foreground"
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
