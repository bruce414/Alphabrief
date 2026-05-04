export function Process() {
  return (
    <section className="border-y border-border bg-muted/30 px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-medium text-primary">How it works</p>
          <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
            Three steps. Infinite insights.
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            Transform any input into comprehensive market research in minutes.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Step 1 */}
          <div className="relative">
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background">
                I
              </div>
              <div className="hidden h-px flex-1 bg-border lg:block" />
            </div>
            <h3 className="mb-3 text-xl font-semibold">Input your source</h3>
            <p className="mb-6 text-muted-foreground">
              Paste text, enter a URL, or upload documents. Our system handles PDFs, articles, videos, and more.
            </p>
            <div className="rounded-lg border border-border bg-card p-4 font-mono text-sm">
              <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                <span className="h-3 w-3 rounded-full bg-red-400" />
                <span className="h-3 w-3 rounded-full bg-yellow-400" />
                <span className="h-3 w-3 rounded-full bg-green-400" />
              </div>
              <code className="text-muted-foreground">
                <span className="text-primary">$</span> insight analyze --url <span className="text-green-600">&quot;bloomberg.com/ev-market&quot;</span>
              </code>
            </div>
          </div>

          {/* Step 2 */}
          <div className="relative">
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background">
                II
              </div>
              <div className="hidden h-px flex-1 bg-border lg:block" />
            </div>
            <h3 className="mb-3 text-xl font-semibold">AI researches & analyzes</h3>
            <p className="mb-6 text-muted-foreground">
              Our multi-step agent extracts data, researches competitors, identifies trends, and validates findings.
            </p>
            <div className="space-y-2 rounded-lg border border-border bg-card p-4 text-sm">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                <span className="text-muted-foreground">Extracting key entities...</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                <span className="text-muted-foreground">Researching competitors...</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                <span className="text-muted-foreground">Identifying market trends...</span>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative">
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background">
                III
              </div>
            </div>
            <h3 className="mb-3 text-xl font-semibold">Get structured report</h3>
            <p className="mb-6 text-muted-foreground">
              Receive organized insights with executive summary, key findings, trends, competitors, and cited sources.
            </p>
            <div className="space-y-2 rounded-lg border border-border bg-card p-4 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">Executive Summary</span>
                <span className="text-xs text-green-600">Complete</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium">Key Insights</span>
                <span className="text-xs text-green-600">5 found</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium">Competitor Analysis</span>
                <span className="text-xs text-green-600">4 analyzed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
