import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/components/layout/app-layout'
import { AppSectionPage } from '@/pages/app-section-page'
import { LandingPage } from '@/pages/landing-page'
import { NotFoundPage } from '@/pages/not-found-page'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/app" element={<AppLayout />}>
        <Route index element={<Navigate to="/app/ask" replace />} />
        <Route
          path="ask"
          element={
            <AppSectionPage
              title="Ask"
              description="Pose questions against your sources and briefs."
            />
          }
        />
        <Route
          path="research"
          element={
            <AppSectionPage
              title="Research"
              description="Deeper workflows for filings, calls, and notes."
            />
          }
        />
        <Route
          path="reflection"
          element={
            <AppSectionPage
              title="Reflection"
              description="Review and refine takeaways over time."
            />
          }
        />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
