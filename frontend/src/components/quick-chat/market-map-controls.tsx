import {
  Maximize2,
  Minus,
  PanelRightClose,
  Plus,
} from 'lucide-react'
import { useReactFlow } from '@xyflow/react'

import { Button } from '@/components/ui/button'

export type MarketMapControlsProps = {
  onCollapse: () => void
}

export function MarketMapControls({ onCollapse }: MarketMapControlsProps) {
  const { zoomIn, zoomOut, fitView } = useReactFlow()

  return (
    <div className="absolute right-3 top-3 z-10 flex items-center gap-1 rounded-lg border border-border bg-white/95 p-1 shadow-sm backdrop-blur-sm">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => zoomIn({ duration: 200 })}
        aria-label="Zoom in"
      >
        <Plus className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => zoomOut({ duration: 200 })}
        aria-label="Zoom out"
      >
        <Minus className="h-4 w-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => fitView({ padding: 0.2, duration: 300 })}
        aria-label="Reset view"
      >
        <Maximize2 className="h-4 w-4" />
      </Button>
      <span className="mx-0.5 h-5 w-px bg-border" aria-hidden />
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={onCollapse}
        aria-label="Collapse market map panel"
      >
        <PanelRightClose className="h-4 w-4" />
      </Button>
    </div>
  )
}
