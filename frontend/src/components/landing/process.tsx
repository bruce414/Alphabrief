export function Process() {
  return (
    <section
      id="process"
      className="scroll-mt-20 border-y border-border bg-muted/30 px-6 py-24 md:py-32"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <p className="mb-3 text-sm font-medium text-primary">How it works</p>
          <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
            Three steps to a clearer brief
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            A simple flow from inputs you trust to a structured readout you can
            share or file away.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="relative">
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background">
                I
              </div>
              <div className="hidden h-px flex-1 bg-border lg:block" />
            </div>
            <h3 className="mb-3 text-xl font-semibold">Add your sources</h3>
            <p className="mb-6 text-muted-foreground">
              Paste a URL, drop notes, or point at documents. Start from what you
              are already reading—no new habits required.
            </p>
            <div className="rounded-lg border border-border bg-card p-4 font-mono text-sm">
              <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                <span className="h-3 w-3 rounded-full bg-red-400/90" />
                <span className="h-3 w-3 rounded-full bg-yellow-400/90" />
                <span className="h-3 w-3 rounded-full bg-green-500/80" />
              </div>
              <code className="block text-left text-muted-foreground">
                <span className="text-primary">$</span> alphabrief create{' '}
                <span className="text-emerald-700">
                  --source &quot;https://example.com/filing&quot;
                </span>
              </code>
            </div>
          </div>

          <div className="relative">
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background">
                II
              </div>
              <div className="hidden h-px flex-1 bg-border lg:block" />
            </div>
            <h3 className="mb-3 text-xl font-semibold">
              Analysis stays grounded
            </h3>
            <p className="mb-6 text-muted-foreground">
              The product direction is source-aware synthesis: cross-reference
              what you provided, surface tensions, and avoid hand-wavy claims.
            </p>
            <div className="space-y-2 rounded-lg border border-border bg-card p-4 text-left text-sm">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-primary/70" />
                <span className="text-muted-foreground">
                  Map entities & themes…
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-primary/70" />
                <span className="text-muted-foreground">
                  Trace claims to sources…
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-primary/70" />
                <span className="text-muted-foreground">
                  Draft structured sections…
                </span>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="mb-6 flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-foreground text-lg font-bold text-background">
                III
              </div>
            </div>
            <h3 className="mb-3 text-xl font-semibold">Read the brief</h3>
            <p className="mb-6 text-muted-foreground">
              Get a structured AlphaBrief you can skim before deep dives—suited
              for notes, handoffs, and follow-up questions.
            </p>
            <div className="space-y-2 rounded-lg border border-border bg-card p-4 text-left text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">Executive overview</span>
                <span className="text-xs text-muted-foreground">Ready</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium">Key themes</span>
                <span className="text-xs text-muted-foreground">Ready</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium">Sources & citations</span>
                <span className="text-xs text-muted-foreground">Ready</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
