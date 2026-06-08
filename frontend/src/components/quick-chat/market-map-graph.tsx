import { useCallback, useEffect, useMemo } from 'react'
import {
  Background,
  MarkerType,
  ReactFlow,
  useReactFlow,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { layoutMarketMapGraph } from '@/components/quick-chat/market-map-layout'
import { MarketMapFlowNode } from '@/components/quick-chat/market-map-node'
import type { MarketMap } from '@/components/quick-chat/types'

const nodeTypes = {
  marketMapNode: MarketMapFlowNode,
}

function marketMapToFlow(marketMap: MarketMap): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = marketMap.nodes.map((n) => ({
    id: n.id,
    type: 'marketMapNode',
    position: { x: 0, y: 0 },
    data: { label: n.label, nodeType: n.type },
    draggable: false,
    selectable: true,
  }))

  const edges: Edge[] = marketMap.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.label,
    type: 'smoothstep',
    animated: false,
    selectable: false,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 14,
      height: 14,
      color: 'hsl(215 16% 55%)',
    },
    labelStyle: {
      fontSize: 10,
      fontWeight: 500,
      fill: 'hsl(222 47% 11%)',
    },
    labelBgStyle: {
      fill: 'hsl(210 20% 98%)',
      fillOpacity: 0.92,
    },
    labelBgPadding: [6, 3] as [number, number],
    labelBgBorderRadius: 4,
    style: {
      stroke: 'hsl(215 16% 72%)',
      strokeWidth: 1.25,
    },
  }))

  return {
    nodes: layoutMarketMapGraph(nodes, edges),
    edges,
  }
}

type MarketMapGraphCanvasProps = {
  marketMap: MarketMap
  selectedNodeId: string | null
  onNodeSelect: (nodeId: string) => void
}

function MarketMapGraphCanvas({
  marketMap,
  selectedNodeId,
  onNodeSelect,
}: MarketMapGraphCanvasProps) {
  const { fitView } = useReactFlow()
  const { nodes, edges } = useMemo(
    () => marketMapToFlow(marketMap),
    [marketMap],
  )

  const nodesWithSelection = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        selected: n.id === selectedNodeId,
      })),
    [nodes, selectedNodeId],
  )

  useEffect(() => {
    const timer = window.setTimeout(() => {
      fitView({ padding: 0.2, duration: 300 })
    }, 50)
    return () => window.clearTimeout(timer)
  }, [fitView, marketMap])

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      onNodeSelect(node.id)
    },
    [onNodeSelect],
  )

  const onPaneClick = useCallback(() => {
    onNodeSelect('')
  }, [onNodeSelect])

  return (
    <ReactFlow
      nodes={nodesWithSelection}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable
      panOnScroll
      zoomOnScroll
      minZoom={0.25}
      maxZoom={1.75}
      proOptions={{ hideAttribution: true }}
      className="h-full w-full bg-white"
    >
      <Background gap={20} size={1} color="hsl(214 20% 92%)" />
    </ReactFlow>
  )
}

export type MarketMapGraphProps = {
  marketMap: MarketMap
  selectedNodeId: string | null
  onNodeSelect: (nodeId: string) => void
}

export function MarketMapGraph(props: MarketMapGraphProps) {
  return <MarketMapGraphCanvas {...props} />
}
