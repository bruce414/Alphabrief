import { apiFetch } from '@/lib/api'
import type {
  MarketMap,
  MarketMapConfidence,
  MarketMapNode,
  MarketMapNodeType,
} from '@/components/quick-chat/types'

export type QuickChatAnalysis = {
  summary: string
  whyItMatters: string
  marketImpact: string
  risksAndUncertainties: string
  watchNext: string[]
}

export type AnalyzeSourceParams = {
  sourceUrl?: string
  sourceText?: string
  userQuery?: string
}

export type AnalyzeSourceSuccess = {
  ok: true
  analysis: QuickChatAnalysis
  marketMap: MarketMap
}

export type AnalyzeSourceFailure = {
  ok: false
  errorCode: string
  message: string
}

export type AnalyzeSourceResult = AnalyzeSourceSuccess | AnalyzeSourceFailure

type RawAnalysis = {
  summary: string
  why_it_matters: string
  market_impact: string
  risks_and_uncertainties: string
  watch_next: string[]
}

type RawMarketMapNode = {
  id: string
  type: MarketMapNodeType
  label: string
  description: string
  linked_section?: string
  linkedSection?: string
  confidence?: MarketMapConfidence
}

type RawMarketMap = {
  nodes: RawMarketMapNode[]
  edges: MarketMap['edges']
}

type RawSuccessBody = {
  analysis: RawAnalysis
  marketMap: RawMarketMap
}

type RawErrorBody = {
  error: {
    errorCode: string
    message: string
  }
}

function normalizeAnalysis(raw: RawAnalysis): QuickChatAnalysis {
  return {
    summary: raw.summary,
    whyItMatters: raw.why_it_matters,
    marketImpact: raw.market_impact,
    risksAndUncertainties: raw.risks_and_uncertainties,
    watchNext: raw.watch_next ?? [],
  }
}

function normalizeNode(raw: RawMarketMapNode): MarketMapNode {
  return {
    id: raw.id,
    type: raw.type,
    label: raw.label,
    description: raw.description,
    linkedSection: raw.linkedSection ?? raw.linked_section,
    confidence: raw.confidence,
  }
}

function normalizeMarketMap(raw: RawMarketMap): MarketMap {
  return {
    nodes: raw.nodes.map(normalizeNode),
    edges: raw.edges,
  }
}

export async function analyzeSource(
  params: AnalyzeSourceParams,
): Promise<AnalyzeSourceResult> {
  const data = await apiFetch<RawSuccessBody | RawErrorBody>('/quick-chat/analyze', {
    method: 'POST',
    body: JSON.stringify({
      sourceUrl: params.sourceUrl,
      sourceText: params.sourceText,
      userQuery: params.userQuery,
    }),
  })

  if ('error' in data && data.error) {
    return {
      ok: false,
      errorCode: data.error.errorCode,
      message: data.error.message,
    }
  }

  if (!('analysis' in data) || !data.analysis || !data.marketMap) {
    return {
      ok: false,
      errorCode: 'INVALID_RESPONSE',
      message: 'Unexpected response from analysis service',
    }
  }

  return {
    ok: true,
    analysis: normalizeAnalysis(data.analysis),
    marketMap: normalizeMarketMap(data.marketMap),
  }
}
