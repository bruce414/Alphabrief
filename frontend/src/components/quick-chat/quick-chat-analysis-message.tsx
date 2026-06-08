import type { QuickChatAnalysis } from '@/lib/quickChatApi'

const SECTIONS: {
  key: keyof QuickChatAnalysis
  title: string
  list?: boolean
}[] = [
  { key: 'summary', title: 'Summary' },
  { key: 'whyItMatters', title: 'Why it matters' },
  { key: 'marketImpact', title: 'Market impact' },
  { key: 'risksAndUncertainties', title: 'Risks and uncertainties' },
  { key: 'watchNext', title: 'What to watch next', list: true },
]

export type QuickChatAnalysisMessageProps = {
  analysis: QuickChatAnalysis
  sourceUrl?: string | null
}

export function QuickChatAnalysisMessage({
  analysis,
  sourceUrl,
}: QuickChatAnalysisMessageProps) {
  return (
    <div className="flex flex-col gap-3">
      {sourceUrl ? (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-primary underline-offset-2 hover:underline"
        >
          View source
        </a>
      ) : null}

      {SECTIONS.map(({ key, title, list }) => {
        const value = analysis[key]
        if (list) {
          const items = Array.isArray(value) ? value : []
          if (items.length === 0) return null
          return (
            <section
              key={key}
              className="rounded-xl border border-border bg-card px-3.5 py-3 shadow-sm"
            >
              <h3 className="mb-2 text-[11px] font-bold uppercase tracking-[0.06em] text-muted-foreground">
                {title}
              </h3>
              <ul className="list-inside list-disc space-y-1 text-[13px] leading-relaxed text-foreground">
                {items.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            </section>
          )
        }

        const text = typeof value === 'string' ? value.trim() : ''
        if (!text) return null

        return (
          <section
            key={key}
            className="rounded-xl border border-border bg-card px-3.5 py-3 shadow-sm"
          >
            <h3 className="mb-1.5 text-[11px] font-bold uppercase tracking-[0.06em] text-muted-foreground">
              {title}
            </h3>
            <p className="text-[13px] leading-relaxed text-foreground">{text}</p>
          </section>
        )
      })}
    </div>
  )
}

