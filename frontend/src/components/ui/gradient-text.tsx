import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

type GradientTextProps = {
  children: ReactNode
  className?: string
}

export function GradientText({ children, className }: GradientTextProps) {
  return (
    <span
      className={cn(
        'bg-gradient-to-r from-slate-700 via-slate-600 to-slate-800 bg-clip-text text-transparent dark:from-slate-200 dark:via-slate-300 dark:to-slate-200',
        className,
      )}
    >
      {children}
    </span>
  )
}
