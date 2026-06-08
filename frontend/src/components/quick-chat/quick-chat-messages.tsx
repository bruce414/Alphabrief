import { QuickChatAnalysisMessage } from '@/components/quick-chat/quick-chat-analysis-message'
import type { QuickChatSessionPhase } from '@/components/quick-chat/types'
import type { QuickChatAnalysis } from '@/lib/quickChatApi'

function FinoraAvatar() {
  return (
    <div className="flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[5px] bg-foreground">
      <svg
        width="10"
        height="10"
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <path d="M50 15 L78 78 L50 62 L22 78 Z" fill="white" />
        <path
          d="M50 62 L22 78 Q35 68 50 72 Q65 68 78 78 Z"
          fill="rgba(255,255,255,0.35)"
        />
      </svg>
    </div>
  )
}

export type QuickChatMessagesProps = {
  userMessage: string
  phase: QuickChatSessionPhase
  analysis: QuickChatAnalysis | null
  errorMessage: string | null
  sourceUrl: string | null
}

export function QuickChatMessages({
  userMessage,
  phase,
  analysis,
  errorMessage,
  sourceUrl,
}: QuickChatMessagesProps) {
  const isLoading = phase === 'loading'
  const isError = phase === 'error'
  const isReady = phase === 'ready'

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-y-auto bg-white px-6 py-6">
      <div className="mb-4 flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-xl bg-foreground px-3.5 py-2.5 text-[13px] leading-relaxed text-background">
          {userMessage}
        </div>
      </div>

      <div className="mb-2 max-w-2xl">
        <div className="mb-2 flex items-center gap-1.5">
          <FinoraAvatar />
          <span className="text-[10px] font-bold uppercase tracking-[0.06em] text-foreground">
            Finora
          </span>
        </div>

        {isLoading ? (
          <div className="flex items-center gap-1.5 text-[13px] text-muted-foreground">
            <span
              className="h-1.5 w-1.5 shrink-0 animate-pulse rounded-full bg-muted-foreground/50"
              aria-hidden
            />
            Analyzing...
          </div>
        ) : null}

        {isError && errorMessage ? (
          <p className="rounded-xl border border-destructive/30 bg-destructive/5 px-3.5 py-2.5 text-[13px] leading-relaxed text-destructive">
            {errorMessage}
          </p>
        ) : null}

        {isReady && analysis ? (
          <QuickChatAnalysisMessage analysis={analysis} sourceUrl={sourceUrl} />
        ) : null}

        {isReady && !analysis && !errorMessage ? (
          <p className="text-[13px] leading-relaxed text-muted-foreground">
            Ask a finance question or paste a news article to get started.
          </p>
        ) : null}
      </div>
    </div>
  )
}
