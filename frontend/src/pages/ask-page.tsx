import { Check, ChevronDown, Loader2 } from 'lucide-react'
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { MOCK_RECENT_BRIEFS, type RecentBrief } from '@/data/recent-briefs-mock'
import { cn } from '@/lib/utils'

const PLACEHOLDER =
  "Nvidia Blackwell ramp — what's the latest from supply-chain checks?"

const SUGGESTIONS = [
  'Compare TSMC and Samsung foundry roadmap',
  'Summarize this earnings call',
  'Find risks in my GLP-1 thesis',
  'What changed in uranium this week?',
] as const

const INPUT_MODES = [
  'Ask',
  'Company',
  'Market',
  'Brief',
  'URL',
  'YouTube',
] as const

type InputMode = (typeof INPUT_MODES)[number]

const RESEARCH_MODES = [
  {
    id: 'quick' as const,
    triggerLabel: 'Quick',
    title: 'Quick research',
    badge: '~30s',
    subtitle: 'Fast scan · 3–5 sources',
  },
  {
    id: 'standard' as const,
    triggerLabel: 'Standard',
    title: 'Standard research',
    badge: '~2m',
    subtitle: 'Balanced depth · 10–15 sources',
  },
  {
    id: 'deep' as const,
    triggerLabel: 'Deep',
    title: 'Deep research',
    badge: '~6m',
    subtitle: 'Multi-pass · 25+ sources',
  },
] as const

type ResearchModeId = (typeof RESEARCH_MODES)[number]['id']

function ResearchModeDots() {
  return (
    <span
      className="grid shrink-0 grid-cols-2 gap-0.5 place-self-center"
      aria-hidden
    >
      {Array.from({ length: 4 }).map((_, i) => (
        <span key={i} className="h-1 w-1 rounded-full bg-violet-500" />
      ))}
    </span>
  )
}

type ResearchModeMenuProps = {
  value: ResearchModeId
  onChange: (id: ResearchModeId) => void
}

function ResearchModeMenu({ value, onChange }: ResearchModeMenuProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  const active = RESEARCH_MODES.find((m) => m.id === value) ?? RESEARCH_MODES[0]

  useEffect(() => {
    if (!open) return
    const onDocMouseDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDocMouseDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocMouseDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div ref={rootRef} className="relative shrink-0">
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label="Research mode"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          'flex h-10 items-center gap-2 rounded-full border-2 border-blue-700 bg-background px-3.5 pl-3 text-sm font-bold text-foreground shadow-sm transition-colors',
          'hover:bg-muted/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600/40 focus-visible:ring-offset-2',
        )}
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-violet-200/80 bg-violet-50/80">
          <ResearchModeDots />
        </span>
        <span className="min-w-[3.25rem] text-left">{active.triggerLabel}</span>
        <ChevronDown
          className={cn(
            'h-4 w-4 shrink-0 text-foreground/70 transition-transform',
            open && 'rotate-180',
          )}
          aria-hidden
        />
      </button>

      {open ? (
        <div
          className="absolute left-0 top-full z-[100] mt-2 w-[min(100vw-2rem,20rem)] rounded-xl border border-border/80 bg-card py-2 shadow-lg shadow-black/10 ring-1 ring-black/[0.04]"
          role="listbox"
          aria-label="Research mode"
        >
          <p className="px-3 pb-2 pt-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-violet-500/90">
            Research mode
          </p>
          <ul className="max-h-[min(70vh,22rem)] overflow-y-auto px-1 pb-1">
            {RESEARCH_MODES.map((m) => {
              const selected = m.id === value
              return (
                <li key={m.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={selected}
                    onClick={() => {
                      onChange(m.id)
                      setOpen(false)
                    }}
                    className={cn(
                      'flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left transition-colors',
                      selected
                        ? 'bg-slate-100/95'
                        : 'hover:bg-muted/60',
                    )}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold tracking-tight text-foreground">
                          {m.title}
                        </span>
                        <span className="rounded-full border border-border bg-muted/60 px-2 py-0.5 text-[11px] font-medium tabular-nums text-muted-foreground">
                          {m.badge}
                        </span>
                      </div>
                      <p className="mt-0.5 text-xs leading-relaxed text-muted-foreground">
                        {m.subtitle}
                      </p>
                    </div>
                    {selected ? (
                      <Check
                        className="mt-0.5 h-4 w-4 shrink-0 text-violet-600"
                        strokeWidth={2.5}
                        aria-hidden
                      />
                    ) : (
                      <span className="w-4 shrink-0" aria-hidden />
                    )}
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
      ) : null}
    </div>
  )
}

function formatStatusPill(date: Date) {
  const weekday = date.toLocaleDateString('en-US', { weekday: 'long' })
  const month = date.toLocaleDateString('en-US', { month: 'long' })
  const day = date.toLocaleDateString('en-US', { day: '2-digit' })
  return `${weekday} · ${month} ${day} · ready when you are`
}

function RecentBriefsBlock({ items }: { items: readonly RecentBrief[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border/80 bg-muted/20 px-4 py-8 text-center">
        <p className="text-sm font-medium text-foreground">No briefs yet</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Generated analyses will appear here with tags and sources.
        </p>
      </div>
    )
  }

  return (
    <ul className="divide-y divide-border/80">
      {items.map((brief) => (
        <li key={brief.id}>
          <button
            type="button"
            className="flex w-full flex-col gap-3 rounded-lg py-4 text-left transition-colors hover:bg-muted/30 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-1"
          >
            <div className="min-w-0 flex-1 space-y-2">
              <p className="font-medium leading-snug tracking-tight text-foreground">
                {brief.title}
              </p>
              <div className="flex flex-wrap items-center gap-1.5">
                {brief.tags.map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="border border-border/60 bg-background/80 font-normal text-muted-foreground"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-4 text-sm text-muted-foreground sm:flex-col sm:items-end sm:gap-1 sm:text-right">
              <span className="tabular-nums">{brief.sourceCount} src</span>
              <span className="tabular-nums text-xs sm:text-sm">
                {brief.createdLabel}
              </span>
            </div>
          </button>
        </li>
      ))}
    </ul>
  )
}

export function AskPage() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<InputMode>('Ask')
  const [researchMode, setResearchMode] = useState<ResearchModeId>('quick')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const statusLine = useMemo(() => formatStatusPill(new Date()), [])

  const onSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault()
      if (isSubmitting) return
      setIsSubmitting(true)
      window.setTimeout(() => {
        setIsSubmitting(false)
      }, 1400)
    },
    [isSubmitting],
  )

  const applySuggestion = useCallback((text: string) => {
    setQuery(text)
  }, [])

  const canSubmit = query.trim().length > 0

  return (
    <div className="relative pb-20 pt-6 md:pt-10">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[min(560px,70svh)] bg-[radial-gradient(ellipse_90%_60%_at_50%_-10%,rgba(139,92,246,0.12),rgba(99,102,241,0.04)_42%,transparent_68%)]"
        aria-hidden
      />
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-48 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-200/35 via-transparent to-transparent" />

      <div className="mx-auto flex w-full max-w-6xl flex-col items-center px-4 sm:px-6">
        <div className="mx-auto flex w-full max-w-3xl flex-col items-center">
          <p
            className={cn(
              'mb-6 hidden items-center gap-2 rounded-full border border-border/80 bg-muted/40 px-4 py-1.5 text-sm text-muted-foreground sm:inline-flex',
            )}
          >
            <span
              className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_0_3px_rgba(34,197,94,0.12)]"
              aria-hidden
            />
            {statusLine}
          </p>

          <h1 className="text-balance text-center text-3xl font-bold tracking-tight text-foreground md:text-4xl md:leading-[1.12]">
            What would you like to{' '}
            <span className="bg-gradient-to-r from-violet-600 via-violet-500 to-indigo-600 bg-clip-text text-transparent">
              research
            </span>
            ?
          </h1>

          <p className="mt-4 max-w-xl text-balance text-center text-base leading-relaxed text-muted-foreground md:text-lg">
            Drop in a company, market, URL, PDF, or video and get a structured
            brief with insights, risks, and cited sources.
          </p>
        </div>

        <Card className="mt-10 w-full overflow-visible border-border/80 bg-card/80 p-5 shadow-[0_1px_2px_rgba(15,23,42,0.04),0_14px_40px_-18px_rgba(99,102,241,0.22)] backdrop-blur-sm md:p-6">
          <form onSubmit={onSubmit} className="overflow-visible">
            <label htmlFor="ask-query" className="sr-only">
              Research prompt
            </label>
            <textarea
              id="ask-query"
              name="query"
              rows={4}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={PLACEHOLDER}
              className="w-full resize-y border-0 bg-transparent text-[0.97rem] leading-relaxed text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-0 md:text-base"
            />

            <div className="mt-4 flex min-w-0 flex-nowrap items-center justify-between gap-3 border-t border-border/80 pt-4">
              <div className="min-w-0 flex-1 overflow-x-auto overflow-y-visible [-webkit-overflow-scrolling:touch]">
                <div className="flex w-max min-w-0 flex-nowrap items-center gap-1.5 pr-2 md:gap-2">
                {INPUT_MODES.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setMode(m)}
                    className={cn(
                      'shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium tracking-tight transition-colors md:text-[13px]',
                      mode === m
                        ? 'border-border bg-muted text-foreground shadow-sm'
                        : 'border-transparent text-muted-foreground hover:border-border/60 hover:bg-muted/50 hover:text-foreground',
                    )}
                  >
                    {m}
                  </button>
                ))}
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-2 overflow-visible">
                <ResearchModeMenu
                  value={researchMode}
                  onChange={setResearchMode}
                />
                <Button
                  type="submit"
                  disabled={!canSubmit || isSubmitting}
                  className="h-10 shrink-0 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 px-5 text-sm font-semibold text-white shadow-md shadow-violet-500/20 transition-opacity hover:opacity-95 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2
                        className="mr-2 h-4 w-4 animate-spin"
                        aria-hidden
                      />
                      Generating…
                    </>
                  ) : (
                    'Generate analysis'
                  )}
                </Button>
              </div>
            </div>
          </form>
        </Card>

        <div className="mt-5 flex w-full max-w-6xl flex-wrap justify-center gap-2">
          {SUGGESTIONS.map((text) => (
            <button
              key={text}
              type="button"
              onClick={() => applySuggestion(text)}
              className="rounded-full border border-border/80 bg-background/90 px-3.5 py-1.5 text-left text-xs font-medium leading-snug text-muted-foreground transition-colors hover:border-violet-200/80 hover:text-foreground md:text-[13px]"
            >
              {text}
            </button>
          ))}
        </div>

        <section className="mt-16 w-full md:mt-20">
          <div className="flex flex-col gap-1 border-b border-border/80 pb-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold tracking-tight text-foreground">
                Recent briefs
              </h2>
              <p className="mt-0.5 text-xs text-muted-foreground sm:text-sm">
                Latest analyses from your workspace
              </p>
            </div>
          </div>
          <RecentBriefsBlock items={MOCK_RECENT_BRIEFS} />
        </section>
      </div>
    </div>
  )
}
