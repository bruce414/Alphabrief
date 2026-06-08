export type AnalysisMode = 'chat_only' | 'source_analysis_with_map'

export type QuickChatSessionPhase = 'idle' | 'loading' | 'ready' | 'error'

export const MAP_LOADING_STAGES = [
  'Source detected',
  'Extracting entities...',
  'Mapping relationships...',
] as const

export type MarketMapConfidence = 'low' | 'medium' | 'high'

export type MarketMapNodeType =
  | 'main_event'
  | 'company'
  | 'sector_theme'
  | 'market_impact'
  | 'risk_uncertainty'
  | 'watch_next'

export type MarketMapNode = {
  id: string
  type: MarketMapNodeType
  label: string
  description: string
  linkedSection?: string
  confidence?: MarketMapConfidence
}

export type MarketMapEdge = {
  id: string
  source: string
  target: string
  label: string
  description?: string
  confidence?: MarketMapConfidence
}

export type MarketMap = {
  nodes: MarketMapNode[]
  edges: MarketMapEdge[]
}
