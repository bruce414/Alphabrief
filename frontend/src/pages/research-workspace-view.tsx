import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  SpaceSidebar,
  type SpaceSidebarTab,
} from '@/components/workspace/space-sidebar'
import { SpaceLoading } from '@/components/workspace/space-loading'
import { useProjects } from '@/hooks/useProjects'
import { T } from '@/styles/tokens'

export function ResearchWorkspaceView() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { projects, isLoading } = useProjects()
  const project = projects.find((p) => p.id === projectId)
  const [activeTab, setActiveTab] = useState<SpaceSidebarTab>('canvas')
  const [introDone, setIntroDone] = useState(false)

  useEffect(() => {
    setIntroDone(false)
  }, [projectId])

  useEffect(() => {
    if (!project || isLoading) return
    const t = window.setTimeout(() => setIntroDone(true), 1500)
    return () => window.clearTimeout(t)
  }, [project, isLoading])

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

  if (!introDone) {
    return <SpaceLoading projectTitle={project.title} />
  }

  return (
    <div style={{ display: 'flex', flex: 1, height: '100vh' }}>
      <SpaceSidebar
        project={project}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onBack={() => navigate('/app/research')}
      />
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
        Canvas + chat coming soon
      </div>
    </div>
  )
}
