import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useSWRConfig } from 'swr'

import { AuthLayout } from '@/components/auth/auth-layout'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { register } from '@/lib/authApi'
import { cn } from '@/lib/utils'

const inputClassName =
  'flex h-11 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50'

export function RegisterPage() {
  const navigate = useNavigate()
  const { mutate } = useSWRConfig()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      await register({
        email: email.trim(),
        password,
        displayName: displayName.trim() || undefined,
      })
      await mutate(['projects'])
      navigate('/app/home', { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Could not create your account. Try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      active="register"
      title="Create your account"
      subtitle="Start with AlphaBrief—research spaces, canvas, and chat in one place."
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="space-y-2">
          <label
            htmlFor="register-name"
            className="text-sm font-medium text-foreground"
          >
            Display name{' '}
            <span className="font-normal text-muted-foreground">(optional)</span>
          </label>
          <input
            id="register-name"
            name="displayName"
            type="text"
            autoComplete="name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className={inputClassName}
            placeholder="Bruce Zhang"
          />
        </div>
        <div className="space-y-2">
          <label
            htmlFor="register-email"
            className="text-sm font-medium text-foreground"
          >
            Email
          </label>
          <input
            id="register-email"
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
            htmlFor="register-password"
            className="text-sm font-medium text-foreground"
          >
            Password
          </label>
          <input
            id="register-password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClassName}
            placeholder="At least 8 characters"
          />
        </div>
        <div className="space-y-2">
          <label
            htmlFor="register-confirm"
            className="text-sm font-medium text-foreground"
          >
            Confirm password
          </label>
          <input
            id="register-confirm"
            name="confirm"
            type="password"
            autoComplete="new-password"
            required
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
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
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link
            to="/login"
            className={cn(
              'font-medium text-foreground underline-offset-4 hover:underline',
            )}
          >
            Sign in
          </Link>
        </p>
      </form>
    </AuthLayout>
  )
}
