import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { InfiniteCanvas } from '@/components/workspace/infinite-canvas'
import { Icon } from '@/components/workspace/icons'
import { SpaceChatPanel } from '@/components/workspace/space-chat-panel'
import {
  SpaceSidebar,
  type SpaceSidebarTab,
} from '@/components/workspace/space-sidebar'
import { SpaceLoading } from '@/components/workspace/space-loading'
import { WorkspaceMemoryPanel } from '@/components/workspace/workspace-memory-panel'
import { WorkspaceSourcesPanel } from '@/components/workspace/workspace-sources-panel'
import { useChats } from '@/hooks/useChats'
import { sortChatsByRecent } from '@/lib/chatSort'
import { useProjects } from '@/hooks/useProjects'
import { T } from '@/styles/tokens'

export function ResearchWorkspaceView() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { projects, isLoading } = useProjects()
  const project = projects.find((p) => p.id === projectId)

  const [activeTab, setActiveTab] = useState<SpaceSidebarTab>('canvas')
  const [loading, setLoading] = useState(true)
  const [aiIntelligenceOn, setAiIntelligenceOn] = useState(true)
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [chatWidth, setChatWidth] = useState(420)
  const resizingRef = useRef<{
    startX: number
    startWidth: number
  } | null>(null)

  const { chats } = useChats(project?.id)

  /** Primary chat for chrome — most recently updated (matches sidebar order). */
  const mostRecentChatId = useMemo(() => {
    if (!chats.length) return null
    const sorted = sortChatsByRecent(chats)
    return sorted[0]?.id ?? null
  }, [chats])

  useEffect(() => {
    setActiveChatId(null)
  }, [projectId])

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
                {/* Fixed overlays (do not move with canvas) */}
                <div
                  style={{
                    position: 'absolute',
                    top: 12,
                    left: 12,
                    zIndex: 20,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    background: T.workspaceTopBar,
                    border: `1px solid ${T.border}`,
                    borderRadius: 12,
                    padding: '6px 14px',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.10)',
                  }}
                >
                  <Icon.Agent style={{ color: T.black }} />
                  <span
                    style={{
                      fontFamily: T.fontSans,
                      fontSize: 12,
                      fontWeight: 600,
                      color: T.black,
                    }}
                  >
                    AI Intelligence
                  </span>
                  <div
                    style={{
                      width: 32,
                      height: 18,
                      background: aiIntelligenceOn ? T.black : T.gray300,
                      borderRadius: 10,
                      position: 'relative',
                      marginLeft: 4,
                      cursor: 'pointer',
                    }}
                    role="switch"
                    aria-checked={aiIntelligenceOn}
                    tabIndex={0}
                    onClick={() => setAiIntelligenceOn((v) => !v)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        setAiIntelligenceOn((v) => !v)
                      }
                    }}
                  >
                    <div
                      style={{
                        position: 'absolute',
                        left: aiIntelligenceOn ? undefined : 2,
                        right: aiIntelligenceOn ? 2 : undefined,
                        top: 2,
                        width: 14,
                        height: 14,
                        borderRadius: '50%',
                        background: 'white',
                      }}
                    />
                  </div>
                </div>

                <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
                  <InfiniteCanvas projectId={project.id} />
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

          {/* Resizer */}
          <div
            role="separator"
            aria-orientation="vertical"
            style={{
              width: 10,
              cursor: 'col-resize',
              background: 'transparent',
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
                setChatWidth(Math.max(380, Math.min(560, next)))
              }
              const onUp = () => {
                resizingRef.current = null
                window.removeEventListener('mousemove', onMove)
                window.removeEventListener('mouseup', onUp)
              }
              window.addEventListener('mousemove', onMove)
              window.addEventListener('mouseup', onUp)
            }}
          >
            {/* no visible divider; just a drag hit-area */}
          </div>

          {/* Chat panel */}
          <div
            key={activeChatId ?? 'no-chat'}
            style={{
              display: 'flex',
              flexDirection: 'column',
              width: chatWidth,
              minWidth: 380,
              maxWidth: 560,
              flexShrink: 0,
              height: '100%',
              minHeight: 0,
            }}
          >
            <SpaceChatPanel
              projectId={project.id}
              chatId={activeChatId}
              onChatReady={(id) => setActiveChatId(id)}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
