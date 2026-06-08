import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'

import type { MarketMapNodeType } from '@/components/quick-chat/types'
import { cn } from '@/lib/utils'

export type MarketMapNodeData = {
  label: string
  nodeType: MarketMapNodeType
}

const TYPE_LABELS: Record<MarketMapNodeType, string> = {
  main_event: 'Main event',
  company: 'Company',
  sector_theme: 'Sector / theme',
  market_impact: 'Market impact',
  risk_uncertainty: 'Risk',
  watch_next: 'Watch next',
}

const TYPE_STYLES: Record<MarketMapNodeType, string> = {
  main_event:
    'min-w-[220px] max-w-[240px] rounded-lg border-2 border-primary bg-card px-3 py-2.5 shadow-sm',
  company:
    'min-w-[180px] max-w-[200px] rounded-2xl border border-border bg-card px-3 py-2 shadow-sm',
  sector_theme:
    'min-w-[180px] max-w-[200px] rounded-md border border-dashed border-muted-foreground/40 bg-muted/30 px-3 py-2',
  market_impact:
    'min-w-[180px] max-w-[200px] rounded-md border border-amber-300/80 bg-amber-50 px-3 py-2 text-amber-950 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-50',
  risk_uncertainty:
    'min-w-[180px] max-w-[200px] rounded-md border border-dashed border-red-400/70 bg-red-50/90 px-3 py-2 text-red-950 dark:border-red-700/60 dark:bg-red-950/35 dark:text-red-50',
  watch_next:
    'min-w-[180px] max-w-[200px] rounded-md border border-blue-300/70 bg-blue-50 px-3 py-2 text-blue-950 dark:border-blue-700/60 dark:bg-blue-950/35 dark:text-blue-50',
}

function MarketMapFlowNodeComponent({ data, selected }: NodeProps) {
  const nodeType = (data?.nodeType ?? 'company') as MarketMapNodeType
  const label = typeof data?.label === 'string' ? data.label : ''

  return (
    <div
      className={cn(
        TYPE_STYLES[nodeType],
        selected && 'ring-2 ring-ring ring-offset-2 ring-offset-background',
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!h-1.5 !w-1.5 !border-muted-foreground/50 !bg-background"
      />
      <p className="mb-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {TYPE_LABELS[nodeType]}
      </p>
      <p
        className={cn(
          'leading-snug text-foreground',
          nodeType === 'main_event' ? 'text-sm font-semibold' : 'text-xs font-medium',
        )}
      >
        {label}
      </p>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!h-1.5 !w-1.5 !border-muted-foreground/50 !bg-background"
      />
    </div>
  )
}

export const MarketMapFlowNode = memo(MarketMapFlowNodeComponent)
