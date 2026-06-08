import { useCallback, useEffect, useRef, useState } from 'react'
import { useOutletContext } from 'react-router-dom'

import { QuickChatHero } from '@/components/quick-chat/quick-chat-hero'
import { QuickChatSplitLayout } from '@/components/quick-chat/quick-chat-split-layout'
import type {
  AnalysisMode,
  MarketMap,
  QuickChatSessionPhase,
} from '@/components/quick-chat/types'
import { buildAnalyzePayload, detectAnalysisMode } from '@/components/quick-chat/utils'
import { analyzeSource } from '@/lib/quickChatApi'
import type { QuickChatAnalysis } from '@/lib/quickChatApi'
import type { AppShellOutletContext } from '@/pages/app-shell'

const HERO_EXIT_MS = 500
const MAP_STAGE_MS = 1500

const ANALYSIS_ERROR_MESSAGE =
  "Couldn't analyze this source — try pasting the article text directly."

export function QuickChatView() {
  const { collapseSidebar } = useOutletContext<AppShellOutletContext>()
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const analysisRequestId = useRef(0)

  const [input, setInput] = useState('')
  const [splitMode, setSplitMode] = useState(false)
  const [heroExiting, setHeroExiting] = useState(false)
  const [layoutVisible, setLayoutVisible] = useState(false)
  const [panelVisible, setPanelVisible] = useState(false)
  const [panelCollapsed, setPanelCollapsed] = useState(false)

  const [userMessage, setUserMessage] = useState('')
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('chat_only')
  const [sessionPhase, setSessionPhase] =
    useState<QuickChatSessionPhase>('idle')
  const [mapLoadingStageIndex, setMapLoadingStageIndex] = useState(0)
  const [analysis, setAnalysis] = useState<QuickChatAnalysis | null>(null)
  const [marketMap, setMarketMap] = useState<MarketMap | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [submittedSourceUrl, setSubmittedSourceUrl] = useState<string | null>(
    null,
  )

  const resetAnalysisState = useCallback(() => {
    setAnalysis(null)
    setMarketMap(null)
    setErrorMessage(null)
    setSubmittedSourceUrl(null)
    setMapLoadingStageIndex(0)
  }, [])

  const startSplitTransition = useCallback(
    (message: string, mode: AnalysisMode) => {
      setUserMessage(message)
      setAnalysisMode(mode)
      setSessionPhase('loading')
      resetAnalysisState()
      setPanelVisible(mode === 'source_analysis_with_map')
      setPanelCollapsed(false)
      collapseSidebar()
      setHeroExiting(true)

      window.setTimeout(() => {
        setSplitMode(true)
      }, HERO_EXIT_MS)
    },
    [collapseSidebar, resetAnalysisState],
  )

  const runSourceAnalysis = useCallback(
    async (trimmed: string) => {
      const requestId = ++analysisRequestId.current
      const payload = buildAnalyzePayload(trimmed)
      setSubmittedSourceUrl(payload.sourceUrl ?? null)

      try {
        const result = await analyzeSource(payload)
        if (analysisRequestId.current !== requestId) return

        if (!result.ok) {
          setSessionPhase('error')
          setErrorMessage(ANALYSIS_ERROR_MESSAGE)
          setPanelVisible(false)
          return
        }

        setAnalysis(result.analysis)
        setMarketMap(result.marketMap)
        setMapLoadingStageIndex(2)
        setSessionPhase('ready')
      } catch {
        if (analysisRequestId.current !== requestId) return
        setSessionPhase('error')
        setErrorMessage(ANALYSIS_ERROR_MESSAGE)
        setPanelVisible(false)
      }
    },
    [],
  )

  const handleMessageSubmit = useCallback(
    async (trimmed: string) => {
      const mode = detectAnalysisMode(trimmed)
      startSplitTransition(trimmed, mode)
      setInput('')

      if (mode === 'source_analysis_with_map') {
        await runSourceAnalysis(trimmed)
      } else {
        setSessionPhase('ready')
      }
    },
    [startSplitTransition, runSourceAnalysis],
  )

  const handleFirstSubmit = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed) return
    void handleMessageSubmit(trimmed)
  }, [input, handleMessageSubmit])

  const handleSubmit = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed) return

    if (!splitMode) {
      handleFirstSubmit()
      return
    }

    void handleMessageSubmit(trimmed)
  }, [input, splitMode, handleFirstSubmit, handleMessageSubmit])

  const applySuggestion = useCallback((text: string) => {
    setInput(text)
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    if (!splitMode) return
    const raf = requestAnimationFrame(() => {
      setLayoutVisible(true)
    })
    return () => cancelAnimationFrame(raf)
  }, [splitMode])

  useEffect(() => {
    if (sessionPhase !== 'loading' || analysisMode !== 'source_analysis_with_map') {
      return
    }

    const stageTimers = [1, 2].map((step) =>
      window.setTimeout(() => {
        setMapLoadingStageIndex((prev) => Math.max(prev, step))
      }, step * MAP_STAGE_MS),
    )

    return () => {
      stageTimers.forEach(window.clearTimeout)
    }
  }, [sessionPhase, analysisMode])

  const showHero = !splitMode
  const mapPanelAvailable = panelVisible
  const mapPanelExpanded = !panelCollapsed

  return (
    <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-white">
      {showHero ? (
        <QuickChatHero
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          onSuggestionClick={applySuggestion}
          exiting={heroExiting}
          inputRef={inputRef}
        />
      ) : null}

      {splitMode ? (
        <QuickChatSplitLayout
          userMessage={userMessage}
          phase={sessionPhase}
          analysisMode={analysisMode}
          mapLoadingStageIndex={mapLoadingStageIndex}
          mapPanelAvailable={mapPanelAvailable}
          mapPanelExpanded={mapPanelExpanded}
          marketMap={marketMap}
          layoutVisible={layoutVisible}
          analysis={analysis}
          errorMessage={errorMessage}
          sourceUrl={submittedSourceUrl}
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          onPanelCollapse={() => setPanelCollapsed(true)}
          onPanelExpand={() => setPanelCollapsed(false)}
        />
      ) : null}
    </div>
  )
}
