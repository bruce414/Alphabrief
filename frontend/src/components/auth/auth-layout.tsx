import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

type AuthLayoutProps = {
  title: string
  subtitle?: string
  children: ReactNode
  /** Highlight which auth route we're on for the header CTAs */
  active?: 'login' | 'register'
}

export function AuthLayout({
  title,
  subtitle,
  children,
  active,
}: AuthLayoutProps) {
  return (
    <div className="relative min-h-svh bg-background">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-200/45 via-transparent to-transparent" />

      <header className="sticky top-0 z-10 border-b border-border/70 bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link
            to="/"
            className="text-xl font-bold tracking-tight text-foreground sm:text-2xl"
          >
            AlphaBrief
          </Link>
          <nav className="flex items-center gap-3 text-sm sm:gap-4">
            <Link
              to="/login"
              className={cn(
                'transition-colors hover:text-foreground motion-reduce:transition-none',
                active === 'login'
                  ? 'font-medium text-foreground'
                  : 'text-muted-foreground',
              )}
            >
              Sign in
            </Link>
            <Button size="sm" className="rounded-full" asChild>
              <Link to="/register">Create account</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-md flex-col px-6 pb-24 pt-12 sm:pt-16">
        <h1 className="mb-2 text-center text-3xl font-bold tracking-tight text-foreground">
          {title}
        </h1>
        {subtitle ? (
          <p className="mb-8 text-center text-muted-foreground">{subtitle}</p>
        ) : (
          <div className="mb-8" />
        )}
        <div className="rounded-2xl border border-border bg-card/80 p-8 shadow-lg shadow-black/[0.04] backdrop-blur-sm">
          {children}
        </div>
      </main>
    </div>
  )
}
