import { useState } from 'react'
import type { FormEvent } from 'react'

import { useAuth } from '@/hooks/useAuth'
import { useLocation, useNavigate } from 'react-router-dom'

type LocationState = {
  from?: {
    pathname: string
  }
}

const LoginPage = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = (location.state as LocationState) ?? {}
  const redirectTo = state.from?.pathname ?? '/'

  const { login, isLoading } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    try {
      await login({ username, password })
      navigate(redirectTo, { replace: true })
    } catch (err) {
      console.error(err)
      setError('Не удалось войти. Проверьте логин и пароль.')
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {error ? (
        <div className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-600">{error}</div>
      ) : null}

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-600" htmlFor="username">
          Логин
        </label>
        <input
          id="username"
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
          placeholder="admin"
          autoComplete="username"
          required
          value={username}
          onChange={(event) => setUsername(event.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-600" htmlFor="password">
          Пароль
        </label>
        <input
          id="password"
          type="password"
          className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
          placeholder="••••••••"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="flex w-full justify-center rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {isLoading ? 'Входим...' : 'Войти'}
      </button>
    </form>
  )
}

export default LoginPage


