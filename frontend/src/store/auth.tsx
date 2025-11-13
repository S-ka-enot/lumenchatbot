import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'

import { authApi, setAuthToken, type LoginPayload, type MeResponse } from '@/lib/api'

export type AuthUser = {
  id: number
  username: string
  isActive: boolean
  telegramId?: number | null
  lastLoginAt?: string | null
}

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<void>
  logout: () => void
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const STORAGE_KEY = 'lumenpay.auth.token'

export const AuthProvider = ({ children }: PropsWithChildren) => {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window === 'undefined') {
      return null
    }
    return window.localStorage.getItem(STORAGE_KEY)
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    if (!token) {
      setAuthToken(null)
      setUser(null)
      setIsLoading(false)
      return
    }

    setAuthToken(token)
    const load = async () => {
      try {
        const profile = await authApi.me()
        setUser(mapAuthUser(profile))
      } catch (error) {
        console.error('Не удалось обновить профиль администратора', error)
        setToken(null)
        setAuthToken(null)
        if (typeof window !== 'undefined') {
          window.localStorage.removeItem(STORAGE_KEY)
        }
      } finally {
        setIsLoading(false)
      }
    }

    void load()
  }, [token])

  const login = useCallback(async (payload: LoginPayload) => {
    setIsLoading(true)
    try {
      const response = await authApi.login(payload)
      const nextToken = response.access_token
      setToken(nextToken)
      setAuthToken(nextToken)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(STORAGE_KEY, nextToken)
      }
      const profile = await authApi.me()
      setUser(mapAuthUser(profile))
    } catch (error) {
      setUser(null)
      setToken(null)
      setAuthToken(null)
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(STORAGE_KEY)
      }
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    setToken(null)
    setAuthToken(null)
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [])

  const refreshProfile = useCallback(async () => {
    if (!token) {
      return
    }
    const profile = await authApi.me()
    setUser(mapAuthUser(profile))
  }, [token])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      refreshProfile,
    }),
    [isLoading, login, logout, refreshProfile, token, user]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

const mapAuthUser = (payload: MeResponse): AuthUser => ({
  id: payload.id,
  username: payload.username,
  isActive: payload.is_active,
  telegramId: payload.telegram_id ?? null,
  lastLoginAt: payload.last_login_at ?? null,
})

export const useAuthContext = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuthContext должен использоваться внутри AuthProvider')
  }
  return context
}


