import { useMemo, useState } from 'react'
import { Outlet, useLocation, useMatch, useNavigate } from 'react-router-dom'

import { MainSidebar } from '@/components/workspace/main-sidebar'
import { T } from '@/styles/tokens'

function currentViewFromPath(pathname: string): 'home' | 'research' | 'discover' {
  if (pathname.startsWith('/app/discover')) return 'discover'
  if (pathname.startsWith('/app/research')) return 'research'
  return 'home'
}

export function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const isWorkspace = Boolean(
    useMatch({ path: '/app/research/:projectId', end: true }),
  )
  const currentView = useMemo(
    () => currentViewFromPath(location.pathname),
    [location.pathname],
  )
  const [activeChatId, setActiveChatId] = useState<string | null>(null)

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: T.bg,
        fontFamily: T.fontSans,
      }}
    >
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        body { font-family: 'DM Sans', system-ui, sans-serif; }
        scrollbar-width: thin;
        scrollbar-color: ${T.gray300} transparent;
      `}</style>
      {!isWorkspace ? (
        <MainSidebar
          currentView={currentView}
          onNavigate={(view) => {
            const paths: Record<typeof view, string> = {
              home: '/app/home',
              research: '/app/research',
              discover: '/app/discover',
            }
            navigate(paths[view])
          }}
          activeChatId={activeChatId}
          onChatSelect={setActiveChatId}
          onNewChat={() => {}}
        />
      ) : null}
      <div
        style={{
          flex: 1,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <Outlet />
      </div>
    </div>
  )
}
