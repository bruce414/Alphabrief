import { useCallback, useEffect, useRef, useState } from 'react'
import { PanelRightOpen } from 'lucide-react'

import { MarketMapPanel } from '@/components/quick-chat/market-map-panel'
import { QuickChatInput } from '@/components/quick-chat/quick-chat-input'
import { QuickChatMessages } from '@/components/quick-chat/quick-chat-messages'
import { Button } from '@/components/ui/button'
import type {
  AnalysisMode,
  MarketMap,
  QuickChatSessionPhase,
} from '@/components/quick-chat/types'
import type { QuickChatAnalysis } from '@/lib/quickChatApi'
import { cn } from '@/lib/utils'

const MAP_PANEL_MIN_PX = 280
const MAP_PANEL_MAX_RATIO = 0.72
const MAP_PANEL_DEFAULT_RATIO = 0.35

export type QuickChatSplitLayoutProps = {
  userMessage: string
  phase: QuickChatSessionPhase
  analysisMode: AnalysisMode
  mapLoadingStageIndex: number
  mapPanelAvailable: boolean
  mapPanelExpanded: boolean
  marketMap: MarketMap | null
  layoutVisible: boolean
  analysis: QuickChatAnalysis | null
  errorMessage: string | null
  sourceUrl: string | null
  input: string
  onInputChange: (value: string) => void
  onSubmit: () => void
  onPanelCollapse: () => void
  onPanelExpand: () => void
}

function clampMapWidth(width: number, containerWidth: number): number {
  const max = Math.max(MAP_PANEL_MIN_PX, containerWidth * MAP_PANEL_MAX_RATIO)
  return Math.min(max, Math.max(MAP_PANEL_MIN_PX, width))
}

export function QuickChatSplitLayout({
  userMessage,
  phase,
  analysisMode,
  mapLoadingStageIndex,
  mapPanelAvailable,
  mapPanelExpanded,
  marketMap,
  layoutVisible,
  analysis,
  errorMessage,
  sourceUrl,
  input,
  onInputChange,
  onSubmit,
  onPanelCollapse,
  onPanelExpand,
}: QuickChatSplitLayoutProps) {
  const showMapPanel = mapPanelAvailable && mapPanelExpanded
  const containerRef = useRef<HTMLDivElement>(null)
  const [mapPanelWidth, setMapPanelWidth] = useState<number | null>(null)
  const resizeRef = useRef<{ startX: number; startWidth: number } | null>(null)

  useEffect(() => {
    if (!showMapPanel) return
    const container = containerRef.current
    if (!container) return

    const applyDefault = () => {
      setMapPanelWidth((prev) => {
        if (prev !== null) return prev
        return clampMapWidth(
          Math.round(container.offsetWidth * MAP_PANEL_DEFAULT_RATIO),
          container.offsetWidth,
        )
      })
    }

    applyDefault()
    const observer = new ResizeObserver(applyDefault)
    observer.observe(container)
    return () => observer.disconnect()
  }, [showMapPanel])

  const handleResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      const container = containerRef.current
      if (!container || mapPanelWidth === null) return

      resizeRef.current = { startX: e.clientX, startWidth: mapPanelWidth }

      const onMove = (ev: MouseEvent) => {
        const state = resizeRef.current
        if (!state) return
        const containerWidth = container.offsetWidth
        const next = clampMapWidth(
          state.startWidth + (state.startX - ev.clientX),
          containerWidth,
        )
        setMapPanelWidth(next)
      }

      const onUp = () => {
        resizeRef.current = null
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
        window.removeEventListener('mousemove', onMove)
        window.removeEventListener('mouseup', onUp)
      }

      document.body.style.cursor = 'col-resize'
      document.body.style.userSelect = 'none'
      window.addEventListener('mousemove', onMove)
      window.addEventListener('mouseup', onUp)
    },
    [mapPanelWidth],
  )

  return (
    <div
      ref={containerRef}
      className={cn(
        'absolute inset-0 flex min-h-0 overflow-hidden bg-white transition-opacity duration-500 ease-out',
        layoutVisible ? 'opacity-100' : 'opacity-0',
      )}
    >
      <section
        className={cn(
          'flex min-w-0 flex-1 flex-col bg-white',
          showMapPanel ? 'min-w-[200px]' : '',
        )}
        aria-label="Chat"
      >
        <header className="flex shrink-0 items-center justify-between gap-2 border-b border-border bg-white px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground">Chat</span>
            <span className="sr-only">Analysis mode: {analysisMode}</span>
          </div>
          {mapPanelAvailable && !mapPanelExpanded ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 px-2.5 text-xs"
              onClick={onPanelExpand}
              aria-label="Show market map"
            >
              <PanelRightOpen className="h-3.5 w-3.5" />
              Market map
            </Button>
          ) : null}
        </header>

        <QuickChatMessages
          userMessage={userMessage}
          phase={phase}
          analysis={analysis}
          errorMessage={errorMessage}
          sourceUrl={sourceUrl}
        />

        <form
          className="shrink-0 border-t border-border bg-white px-4 py-4"
          onSubmit={(e) => {
            e.preventDefault()
            onSubmit()
          }}
        >
          <QuickChatInput
            value={input}
            onChange={onInputChange}
            onSubmit={onSubmit}
            id="quick-chat-split-input"
          />
        </form>
      </section>

      {showMapPanel && mapPanelWidth !== null ? (
        <>
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize market map panel"
            className="group relative z-10 w-2 shrink-0 cursor-col-resize touch-none bg-white"
            onMouseDown={handleResizeStart}
          >
            <span
              className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-border transition-colors group-hover:bg-foreground/25 group-active:bg-foreground/40"
              aria-hidden
            />
          </div>
          <MarketMapPanel
            phase={phase}
            loadingStageIndex={mapLoadingStageIndex}
            visible
            marketMap={marketMap}
            width={mapPanelWidth}
            onCollapse={onPanelCollapse}
          />
        </>
      ) : null}
    </div>
  )
}
