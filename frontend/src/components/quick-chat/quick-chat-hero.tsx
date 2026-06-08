import type { RefObject } from 'react'

import { QuickChatInput } from '@/components/quick-chat/quick-chat-input'
import { cn } from '@/lib/utils'

const SUGGESTIONS = [
  "Explain today's Fed decision",
  'Analyze this Nvidia article',
  'How do rate cuts affect bank stocks?',
  'What is EBITDA?',
] as const

export type QuickChatHeroProps = {
  input: string
  onInputChange: (value: string) => void
  onSubmit: () => void
  onSuggestionClick: (text: string) => void
  exiting?: boolean
  inputRef?: RefObject<HTMLTextAreaElement | null>
}

export function QuickChatHero({
  input,
  onInputChange,
  onSubmit,
  onSuggestionClick,
  exiting = false,
  inputRef,
}: QuickChatHeroProps) {
  return (
    <div
      className={cn(
        'absolute inset-0 flex flex-col items-center justify-center bg-white px-6 py-12',
        'transition-all duration-500 ease-out',
        exiting
          ? 'pointer-events-none translate-y-3 opacity-0'
          : 'translate-y-0 opacity-100',
      )}
    >
      <p className="text-sm font-medium tracking-wide text-muted-foreground">
        Finora
      </p>
      <h1 className="mt-3 max-w-2xl text-balance text-center text-2xl font-semibold leading-snug tracking-tight text-foreground sm:text-3xl sm:leading-tight md:text-[2rem]">
        Paste any financial news. Get the analysis and the market map.
      </h1>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          onSubmit()
        }}
        className="mt-10 w-full max-w-[720px]"
      >
        <QuickChatInput
          value={input}
          onChange={onInputChange}
          onSubmit={onSubmit}
          inputRef={inputRef}
        />
      </form>

      <div className="mt-5 flex max-w-[720px] flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((text) => (
          <button
            key={text}
            type="button"
            onClick={() => onSuggestionClick(text)}
            className="rounded-full border border-border/80 bg-white px-3.5 py-1.5 text-left text-xs font-medium leading-snug text-muted-foreground transition-colors hover:border-foreground/15 hover:bg-muted/40 hover:text-foreground md:text-[13px]"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  )
}
