import { useCallback, useMemo, useState } from 'react'
import { ReactFlowProvider } from '@xyflow/react'

import { MarketMapControls } from '@/components/quick-chat/market-map-controls'
import { MarketMapGraph } from '@/components/quick-chat/market-map-graph'
import { MarketMapNodeDetailDrawer } from '@/components/quick-chat/market-map-node-detail-drawer'
import {
  MAP_LOADING_STAGES,
  type MarketMap,
  type QuickChatSessionPhase,
} from '@/components/quick-chat/types'
import { cn } from '@/lib/utils'

export type MarketMapPanelProps = {
  phase: QuickChatSessionPhase
  loadingStageIndex: number
  visible: boolean
  marketMap: MarketMap | null
  width: number
  onCollapse: () => void
}

export function MarketMapPanel({
  phase,
  loadingStageIndex,
  visible,
  marketMap,
  width,
  onCollapse,
}: MarketMapPanelProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  const isLoading = phase === 'loading'
  const isReady = phase === 'ready' && marketMap !== null
  const stageLabel = MAP_LOADING_STAGES[loadingStageIndex] ?? MAP_LOADING_STAGES[0]

  const selectedNode = useMemo(() => {
    if (!marketMap || !selectedNodeId) return null
    return marketMap.nodes.find((n) => n.id === selectedNodeId) ?? null
  }, [marketMap, selectedNodeId])

  const handleNodeSelect = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId || null)
  }, [])

  const handleCloseDrawer = useCallback(() => {
    setSelectedNodeId(null)
  }, [])

  return (
    <aside
      style={{ width }}
      className={cn(
        'flex h-full shrink-0 flex-col bg-white',
        'transition-transform duration-500 ease-out',
        visible ? 'translate-x-0' : 'translate-x-full',
      )}
      aria-label="Market map"
    >
      <div className="flex shrink-0 items-center justify-between border-b border-border bg-white px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight text-foreground">
          Market Map
        </h2>
      </div>

      <div className="relative min-h-0 flex-1">
        {isLoading ? (
          <div className="flex h-full flex-col items-center justify-center bg-white px-6 py-8">
            <div className="flex w-full max-w-xs flex-col items-center gap-4 text-center">
              <div
                className="h-10 w-10 animate-pulse rounded-full border-2 border-dashed border-muted-foreground/30"
                aria-hidden
              />
              <p
                key={stageLabel}
                className="text-sm font-medium text-foreground transition-opacity duration-300"
              >
                {stageLabel}
              </p>
              <div className="flex gap-1.5" aria-hidden>
                {MAP_LOADING_STAGES.map((_, i) => (
                  <span
                    key={i}
                    className={cn(
                      'h-1.5 w-1.5 rounded-full transition-colors',
                      i === loadingStageIndex
                        ? 'bg-foreground'
                        : 'bg-muted-foreground/30',
                    )}
                  />
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {isReady && marketMap ? (
          <ReactFlowProvider>
            <div className="absolute inset-0">
              <MarketMapGraph
                marketMap={marketMap}
                selectedNodeId={selectedNodeId}
                onNodeSelect={handleNodeSelect}
              />
              <MarketMapControls onCollapse={onCollapse} />
            </div>
            <MarketMapNodeDetailDrawer
              node={selectedNode}
              onClose={handleCloseDrawer}
            />
          </ReactFlowProvider>
        ) : null}
      </div>
    </aside>
  )
}
