import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  InfiniteCanvas,
  useCanvas,
  type InfiniteCanvasHandle,
} from '@/components/workspace/infinite-canvas'
import {
  OnboardingModal,
  readOnboardingDismissed,
  writeOnboardingDismissed,
} from '@/components/workspace/onboarding-modal'
import { CanvasStatusPill } from '@/components/workspace/canvas-status-pill'
import { CanvasViewControls } from '@/components/workspace/canvas-view-controls'
import { SpaceChatPanel } from '@/components/workspace/space-chat-panel'
import {
  SpaceSidebar,
  type SpaceSidebarTab,
} from '@/components/workspace/space-sidebar'
import { SpaceLoading } from '@/components/workspace/space-loading'
import { WorkspaceMemoryPanel } from '@/components/workspace/workspace-memory-panel'
import { WorkspaceOverviewPanel } from '@/components/workspace/workspace-overview-panel'
import { WorkspaceSourcesPanel } from '@/components/workspace/workspace-sources-panel'
import { useChats } from '@/hooks/useChats'
import { useProjectOverview } from '@/hooks/useProjectOverview'
import { sortChatsByRecent } from '@/lib/chatSort'
import { useProjects } from '@/hooks/useProjects'
import { T } from '@/styles/tokens'

/** Minimum chat width so the research mode control stays on one line. */
const CHAT_PANEL_MIN_PX = 468
const CHAT_PANEL_MAX_PX = 560

export function ResearchWorkspaceView() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { projects, isLoading } = useProjects()
  const project = projects.find((p) => p.id === projectId)

  const [activeTab, setActiveTab] = useState<SpaceSidebarTab>('canvas')
  const [loading, setLoading] = useState(true)
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [chatWidth, setChatWidth] = useState(() =>
    Math.min(CHAT_PANEL_MAX_PX, Math.max(CHAT_PANEL_MIN_PX, 480)),
  )
  const resizingRef = useRef<{
    startX: number
    startWidth: number
  } | null>(null)

  const canvasRef = useRef<InfiniteCanvasHandle>(null)
  const chatInputRef = useRef<HTMLTextAreaElement>(null)

  const { chats, isLoading: chatsLoading } = useChats(project?.id)
  const { overview, isLoading: overviewLoading } = useProjectOverview(project?.id)
  const { elements, isLoading: canvasDataLoading } = useCanvas(project?.id)

  const [onboardingDismissed, setOnboardingDismissed] = useState(() =>
    projectId ? readOnboardingDismissed(projectId) : true,
  )

  /** Primary chat for chrome — most recently updated (matches sidebar order). */
  const mostRecentChatId = useMemo(() => {
    if (!chats.length) return null
    const sorted = sortChatsByRecent(chats)
    return sorted[0]?.id ?? null
  }, [chats])

  useEffect(() => {
    setActiveChatId(null)
    setOnboardingDismissed(projectId ? readOnboardingDismissed(projectId) : true)
  }, [projectId])

  const dismissOnboarding = useCallback(() => {
    if (!projectId) return
    writeOnboardingDismissed(projectId)
    setOnboardingDismissed(true)
  }, [projectId])

  const focusChatInput = useCallback(() => {
    window.requestAnimationFrame(() => {
      chatInputRef.current?.focus()
    })
  }, [])

  const showOnboardingModal = useMemo(() => {
    if (!projectId || onboardingDismissed || loading) return false
    if (chatsLoading || overviewLoading || canvasDataLoading) return false
    if (chats.length > 0) return false
    if (elements.length > 0) return false
    if (!overview) return false
    if (overview.includedTopics.length > 0 || overview.targetEntities.length > 0) {
      return false
    }
    return true
  }, [
    projectId,
    onboardingDismissed,
    loading,
    chatsLoading,
    overviewLoading,
    canvasDataLoading,
    chats.length,
    elements.length,
    overview,
  ])

  useEffect(() => {
    if (!activeChatId && mostRecentChatId) setActiveChatId(mostRecentChatId)
  }, [activeChatId, mostRecentChatId])

  useEffect(() => {
    setLoading(true)
  }, [projectId])

  useEffect(() => {
    if (!project || isLoading) return
    const t = window.setTimeout(() => setLoading(false), 1500)
    return () => window.clearTimeout(t)
  }, [project, isLoading, projectId])

  if (isLoading) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: T.gray400,
          fontFamily: T.fontSans,
        }}
      >
        Loading...
      </div>
    )
  }

  if (!project) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: T.gray400,
          fontFamily: T.fontSans,
        }}
      >
        Space not found
      </div>
    )
  }

  if (loading) {
    return <SpaceLoading projectTitle={project.title} />
  }

  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: T.workspaceDashboard,
      }}
    >
      <SpaceSidebar
        project={project}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onBack={() => navigate('/app/research')}
        selectedChatId={activeChatId}
        onSelectChat={(id) => setActiveChatId(id)}
        onCreateCanvasElement={
          activeTab === 'canvas'
            ? (kind) => canvasRef.current?.createElement(kind)
            : undefined
        }
      />

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          background: T.workspaceDashboard,
        }}
      >
        <div
          style={{
            flex: 1,
            display: 'flex',
            overflow: 'hidden',
            minHeight: 0,
          }}
        >
          {/* Canvas column */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minWidth: 0,
              minHeight: 0,
              position: 'relative',
              background: T.workspaceDashboard,
            }}
          >
            {activeTab === 'overview' ? (
              <WorkspaceOverviewPanel project={project} />
            ) : null}
            {activeTab === 'canvas' ? (
              <div
                style={{
                  flex: 1,
                  minHeight: 0,
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  width: '100%',
                }}
              >
                <CanvasViewControls
                  canvasRef={canvasRef}
                  projectId={project.id}
                  chatId={activeChatId}
                />
                <CanvasStatusPill projectId={project.id} />

                <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
                  <InfiniteCanvas
                    ref={canvasRef}
                    projectId={project.id}
                    chatId={activeChatId}
                  />
                </div>
              </div>
            ) : null}
            {activeTab === 'sources' ? (
              <WorkspaceSourcesPanel projectId={project.id} />
            ) : null}
            {activeTab === 'memory' ? (
              <WorkspaceMemoryPanel projectId={project.id} />
            ) : null}
          </div>

          {/* Resizer (drag handle between main column and chat) */}
          <div
            role="separator"
            aria-orientation="vertical"
            style={{
              width: 10,
              cursor: 'col-resize',
              background: T.workspaceDashboard,
              flexShrink: 0,
              position: 'relative',
            }}
            onMouseDown={(e) => {
              e.preventDefault()
              resizingRef.current = { startX: e.clientX, startWidth: chatWidth }
              const onMove = (ev: MouseEvent) => {
                const s = resizingRef.current
                if (!s) return
                const next = s.startWidth + (s.startX - ev.clientX)
                setChatWidth(
                  Math.max(CHAT_PANEL_MIN_PX, Math.min(CHAT_PANEL_MAX_PX, next)),
                )
              }
              const onUp = () => {
                resizingRef.current = null
                window.removeEventListener('mousemove', onMove)
                window.removeEventListener('mouseup', onUp)
              }
              window.addEventListener('mousemove', onMove)
              window.addEventListener('mouseup', onUp)
            }}
          ></div>

          {/* Chat panel */}
          <div
            key={activeChatId ?? 'no-chat'}
            style={{
              display: 'flex',
              flexDirection: 'column',
              width: chatWidth,
              minWidth: CHAT_PANEL_MIN_PX,
              maxWidth: CHAT_PANEL_MAX_PX,
              flexShrink: 0,
              height: '100%',
              minHeight: 0,
              borderLeft: `1px solid ${T.border}`,
            }}
          >
            <SpaceChatPanel
              projectId={project.id}
              chatId={activeChatId}
              chatInputRef={chatInputRef}
              onChatReady={(id) => setActiveChatId(id)}
            />
          </div>
        </div>
      </div>

      <OnboardingModal
        open={showOnboardingModal}
        projectId={project.id}
        onDismiss={dismissOnboarding}
        onFocusChat={focusChatInput}
      />
    </div>
  )
}
