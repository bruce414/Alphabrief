import { Bell, User } from 'lucide-react'
import { Link, NavLink } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useNavDocked } from '@/hooks/use-nav-docked'
import { cn } from '@/lib/utils'

const landingLinks = [
  { label: 'Features', href: '#features' },
  { label: 'How it works', href: '#process' },
  { label: 'Pricing', href: '#pricing' },
] as const

const appLinks = [
  { label: 'Ask', to: '/app/ask' },
  { label: 'Research', to: '/app/research' },
  { label: 'Reflection', to: '/app/reflection' },
] as const

export type SiteNavProps = {
  variant?: 'landing' | 'app'
}

export function SiteNav({ variant = 'landing' }: SiteNavProps) {
  const isDocked = useNavDocked(28)

  return (
    <>
      <header
        className={cn(
          'fixed left-0 right-0 z-50 flex justify-center px-4 sm:px-6',
          'transition-[padding-top] duration-300 ease-out motion-reduce:transition-none',
          isDocked ? 'pt-4' : 'pt-0',
        )}
      >
        <div
          className={cn(
            'flex w-full items-center justify-between gap-2 sm:gap-4',
            'transition-[max-width,background-color,border-color,box-shadow,border-radius,padding-block,margin] duration-300 ease-out motion-reduce:transition-none',
            isDocked
              ? 'max-w-5xl rounded-2xl border border-border/70 bg-background/80 px-4 py-2 shadow-lg shadow-black/[0.06] backdrop-blur-md sm:px-6 sm:py-2.5'
              : 'max-w-7xl border border-transparent bg-transparent py-3 shadow-none sm:px-0',
          )}
        >
          {variant === 'landing' ? (
            <Link
              to="/"
              className="shrink-0 text-xl font-bold tracking-tight text-foreground sm:text-2xl"
            >
              AlphaBrief
            </Link>
          ) : (
            <Link
              to="/app/ask"
              className="shrink-0 text-lg font-bold tracking-tight text-foreground sm:text-xl"
            >
              AlphaBrief
            </Link>
          )}

          {variant === 'landing' ? (
            <nav className="flex min-w-0 flex-1 flex-wrap items-center justify-end gap-x-4 gap-y-2 text-sm text-muted-foreground sm:gap-x-8">
              {landingLinks.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="transition-colors hover:text-foreground motion-reduce:transition-none"
                >
                  {item.label}
                </a>
              ))}
              <Link
                to="/login"
                className="transition-colors hover:text-foreground motion-reduce:transition-none"
              >
                Sign in
              </Link>
              <Button size="sm" className="rounded-full" asChild>
                <Link to="/register">Get started</Link>
              </Button>
            </nav>
          ) : (
            <>
              <nav className="mx-2 flex min-w-0 flex-1 items-center justify-center gap-3 overflow-x-auto text-sm sm:mx-4 sm:gap-8">
                {appLinks.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      cn(
                        'shrink-0 whitespace-nowrap border-b border-transparent pb-0.5 text-muted-foreground transition-colors hover:text-foreground motion-reduce:transition-none',
                        isActive &&
                          'border-foreground/60 text-foreground',
                      )
                    }
                  >
                    {item.label}
                  </NavLink>
                ))}
              </nav>
              <div className="flex shrink-0 items-center gap-0.5 sm:gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  aria-label="Notifications"
                >
                  <Bell className="h-[1.125rem] w-[1.125rem] sm:h-4 sm:w-4" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 sm:h-10 sm:w-10"
                  aria-label="Account"
                >
                  <User className="h-[1.125rem] w-[1.125rem] sm:h-4 sm:w-4" />
                </Button>
              </div>
            </>
          )}
        </div>
      </header>
      <div
        aria-hidden
        className={cn(
          'transition-[min-height] duration-300 ease-out motion-reduce:transition-none',
          isDocked ? 'min-h-[5.5rem]' : 'min-h-16',
        )}
      />
    </>
  )
}
