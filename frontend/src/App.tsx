import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '@/pages/app-shell'
import { HomeView } from '@/pages/home-view'
import { LandingPage } from '@/pages/landing-page'
import { LoginPage } from '@/pages/login-page'
import { NotFoundPage } from '@/pages/not-found-page'
import { RegisterPage } from '@/pages/register-page'
import { ResearchSpacesView } from '@/pages/research-spaces-view'
import { ResearchWorkspaceView } from '@/pages/research-workspace-view'
import { T } from '@/styles/tokens'

function DiscoverPlaceholder() {
  return (
    <div
      style={{
        padding: 24,
        fontFamily: T.fontSans,
        color: T.black,
      }}
    >
      Discover
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/app" element={<AppShell />}>
        <Route index element={<Navigate to="/app/home" replace />} />
        <Route path="home" element={<HomeView />} />
        <Route path="discover" element={<DiscoverPlaceholder />} />
        <Route path="research" element={<ResearchSpacesView />} />
        <Route path="research/:projectId" element={<ResearchWorkspaceView />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
