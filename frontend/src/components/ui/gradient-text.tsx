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
        'bg-gradient-to-r from-slate-700 via-slate-600 to-slate-800 bg-clip-text text-transparent',
        className,
      )}
    >
      {children}
    </span>
  )
}
