import { Menu } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const nav = [
  { label: 'Capabilities', href: '#capabilities' },
  { label: 'How it works', href: '#process' },
  { label: 'Pricing', href: '#pricing' },
] as const

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/80 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-6">
        <Link
          to="/"
          className="text-sm font-semibold tracking-tight text-foreground"
        >
          AlphaBrief
        </Link>

        <nav
          className={cn(
            'hidden items-center gap-6 text-sm text-muted-foreground md:flex',
          )}
        >
          {nav.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="transition-colors hover:text-foreground"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="hidden md:inline-flex"
            asChild
          >
            <a href="#cta">Early access</a>
          </Button>
          <Button size="sm" className="hidden rounded-full md:inline-flex" asChild>
            <a href="#capabilities">Explore</a>
          </Button>
          <Button variant="outline" size="icon" className="md:hidden" asChild>
            <a href="#capabilities" aria-label="Open menu">
              <Menu className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </div>
    </header>
  )
}
