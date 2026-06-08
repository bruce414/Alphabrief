import { Outlet } from 'react-router-dom'

import { SiteNav } from '@/components/layout/site-nav'

export function AppLayout() {
  return (
    <div className="min-h-svh bg-background">
      <SiteNav variant="app" />
      <main className="mx-auto w-full max-w-6xl px-6">
        <Outlet />
      </main>
    </div>
  )
}
