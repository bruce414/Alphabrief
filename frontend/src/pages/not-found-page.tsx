import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-background px-6 py-16">
      <p className="text-sm font-medium text-muted-foreground">404</p>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
        The page you are looking for does not exist or has moved.
      </p>
      <Button className="mt-8 rounded-full" asChild>
        <Link to="/">Go home</Link>
      </Button>
    </div>
  )
}
