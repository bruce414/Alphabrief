import { ArrowUp } from 'lucide-react'
import type { KeyboardEvent, RefObject } from 'react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export type QuickChatInputProps = {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  inputRef?: RefObject<HTMLTextAreaElement | null>
  disabled?: boolean
  id?: string
  className?: string
}

export function QuickChatInput({
  value,
  onChange,
  onSubmit,
  inputRef,
  disabled = false,
  id = 'quick-chat-input',
  className,
}: QuickChatInputProps) {
  const canSend = value.trim().length > 0 && !disabled

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) onSubmit()
    }
  }

  return (
    <div
      className={cn(
        'relative flex items-end rounded-2xl border border-border bg-card shadow-sm',
        'transition-shadow focus-within:border-foreground/20 focus-within:ring-2 focus-within:ring-ring/30 focus-within:ring-offset-2 focus-within:ring-offset-background',
        className,
      )}
    >
      <label htmlFor={id} className="sr-only">
        Ask Finora
      </label>
      <textarea
        ref={inputRef}
        id={id}
        name="message"
        rows={3}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="Paste a URL, paste an article, or ask a market question..."
        className="min-h-[4.5rem] w-full resize-none rounded-2xl border-0 bg-transparent py-4 pl-5 pr-14 text-[0.97rem] leading-relaxed text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-0 disabled:cursor-not-allowed disabled:opacity-60 md:text-base"
      />
      <Button
        type="button"
        size="icon"
        disabled={!canSend}
        aria-label="Send message"
        onClick={onSubmit}
        className={cn(
          'absolute bottom-3 right-3 h-9 w-9 shrink-0 rounded-full',
          canSend
            ? 'bg-primary text-primary-foreground hover:bg-primary/90'
            : 'bg-muted text-muted-foreground',
        )}
      >
        <ArrowUp className="h-4 w-4" strokeWidth={2.25} aria-hidden />
      </Button>
    </div>
  )
}
