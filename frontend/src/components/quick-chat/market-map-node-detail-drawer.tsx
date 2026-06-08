import { X } from 'lucide-react'

import type { MarketMapNode, MarketMapNodeType } from '@/components/quick-chat/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const TYPE_LABELS: Record<MarketMapNodeType, string> = {
  main_event: 'Main event',
  company: 'Company',
  sector_theme: 'Sector / theme',
  market_impact: 'Market impact',
  risk_uncertainty: 'Risk / uncertainty',
  watch_next: 'Watch next',
}

const CONFIDENCE_VARIANT: Record<
  NonNullable<MarketMapNode['confidence']>,
  'default' | 'secondary' | 'outline'
> = {
  high: 'default',
  medium: 'secondary',
  low: 'outline',
}

export type MarketMapNodeDetailDrawerProps = {
  node: MarketMapNode | null
  onClose: () => void
}

export function MarketMapNodeDetailDrawer({
  node,
  onClose,
}: MarketMapNodeDetailDrawerProps) {
  const open = node !== null

  return (
    <aside
      aria-hidden={!open}
      className={cn(
        'absolute inset-y-0 right-0 z-20 flex w-[60%] min-w-[200px] flex-col border-l border-border bg-card shadow-lg transition-transform duration-300 ease-out',
        open ? 'translate-x-0' : 'pointer-events-none translate-x-full',
      )}
    >
      {node ? (
        <>
          <div className="flex shrink-0 items-start justify-between gap-3 border-b border-border px-4 py-3">
            <div>
              <h3 className="text-sm font-semibold leading-snug text-foreground">
                {node.label}
              </h3>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="text-xs text-muted-foreground">
                  {TYPE_LABELS[node.type]}
                </span>
                {node.confidence ? (
                  <Badge
                    variant={CONFIDENCE_VARIANT[node.confidence]}
                    className="text-[10px] font-medium capitalize"
                  >
                    {node.confidence} confidence
                  </Badge>
                ) : null}
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0"
              onClick={onClose}
              aria-label="Close node details"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto px-4 py-4">
            <p className="text-sm leading-relaxed text-muted-foreground">
              {node.description}
            </p>
          </div>
          <div className="shrink-0 border-t border-border px-4 py-3">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </>
      ) : null}
    </aside>
  )
}
