import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSWRConfig } from 'swr'

import { AuthLayout } from '@/components/auth/auth-layout'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { login } from '@/lib/authApi'
import { cn } from '@/lib/utils'

const inputClassName =
  'flex h-11 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

export function LoginPage() {
  const navigate = useNavigate()
  const { mutate } = useSWRConfig()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login({
        email: email.trim(),
        password,
      })
      await mutate(['projects'])
      navigate('/app/home', { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : 'Could not sign in. Try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      active="login"
      title="Welcome back"
      subtitle="Sign in to open your workspace and research spaces."
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="space-y-2">
          <label
            htmlFor="login-email"
            className="text-sm font-medium text-foreground"
          >
            Email
          </label>
          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClassName}
            placeholder="you@company.com"
          />
        </div>
        <div className="space-y-2">
          <label
            htmlFor="login-password"
            className="text-sm font-medium text-foreground"
          >
            Password
          </label>
          <input
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClassName}
          />
        </div>
        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
        <Button
          type="submit"
          size="lg"
          className="mt-1 w-full rounded-full"
          disabled={submitting}
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          No account yet?{' '}
          <Link
            to="/register"
            className={cn(
              'font-medium text-foreground underline-offset-4 hover:underline',
            )}
          >
            Create one
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
