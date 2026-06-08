import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

type AppSectionPageProps = {
  title: string
  description?: string
}

export function AppSectionPage({ title, description }: AppSectionPageProps) {
  return (
    <div className="flex min-h-[calc(100svh-6rem)] flex-col py-12">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        {title}
      </h1>
      {description ? (
        <p className="mt-2 max-w-lg text-muted-foreground">{description}</p>
      ) : null}
      <Button className="mt-10 w-fit rounded-full" variant="outline" asChild>
        <Link to="/">Back to home</Link>
      </Button>
    </div>
  )
}
