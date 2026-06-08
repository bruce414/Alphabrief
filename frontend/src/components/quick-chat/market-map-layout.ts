import dagre from 'dagre'
import type { Edge, Node } from '@xyflow/react'

const NODE_WIDTH = 200
const NODE_HEIGHT = 56
const MAIN_EVENT_WIDTH = 240
const MAIN_EVENT_HEIGHT = 68

export function getMarketMapNodeDimensions(nodeType: string): {
  width: number
  height: number
} {
  if (nodeType === 'main_event') {
    return { width: MAIN_EVENT_WIDTH, height: MAIN_EVENT_HEIGHT }
  }
  return { width: NODE_WIDTH, height: NODE_HEIGHT }
}

export function layoutMarketMapGraph(
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'TB',
): Node[] {
  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({
    rankdir: direction,
    nodesep: 48,
    ranksep: 72,
    marginx: 24,
    marginy: 24,
  })

  nodes.forEach((node) => {
    const nodeType =
      typeof node.data?.nodeType === 'string' ? node.data.nodeType : 'company'
    const { width, height } = getMarketMapNodeDimensions(nodeType)
    graph.setNode(node.id, { width, height })
  })

  edges.forEach((edge) => {
    graph.setEdge(edge.source, edge.target)
  })

  dagre.layout(graph)

  return nodes.map((node) => {
    const positioned = graph.node(node.id)
    const nodeType =
      typeof node.data?.nodeType === 'string' ? node.data.nodeType : 'company'
    const { width, height } = getMarketMapNodeDimensions(nodeType)
    return {
      ...node,
      position: {
        x: positioned.x - width / 2,
        y: positioned.y - height / 2,
      },
    }
  })
}
