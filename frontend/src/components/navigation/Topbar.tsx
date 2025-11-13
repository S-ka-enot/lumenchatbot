import { useMemo } from 'react'

import { useAuth } from '@/hooks/useAuth'
import { Bell, LogOut, Search } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

const getInitials = (value: string | undefined | null) => {
  if (!value) {
    return 'A'
  }
  const parts = value.trim().split(' ')
  if (parts.length === 1) {
    return parts[0]?.charAt(0)?.toUpperCase() ?? 'A'
  }
  return (
    (parts[0]?.charAt(0) ?? '') + (parts[parts.length - 1]?.charAt(0) ?? '')
  ).toUpperCase()
}

const Topbar = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const initials = useMemo(() => getInitials(user?.username), [user?.username])

  const primaryRole = user?.isActive ? 'Администратор' : 'Доступ ограничен'

  const handleLogout = () => {
    logout()
    navigate('/auth/login')
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
        <Search className="h-4 w-4" />
        <input
          className="w-72 border-none bg-transparent text-sm outline-none"
          placeholder="Поиск по участницам или платежам..."
          type="search"
        />
      </div>

      <div className="flex items-center gap-4">
        <button
          type="button"
          className="relative flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-600 transition hover:bg-slate-100"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-1 top-1 h-2.5 w-2.5 rounded-full bg-rose-500" />
        </button>

        <div className="flex items-center gap-3">
          <div className="text-right text-xs">
            <p className="font-semibold text-slate-700">
              {user?.username ?? 'Администратор'}
            </p>
            <p className="text-slate-500">{primaryRole}</p>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
            {initials}
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
        >
          <LogOut className="h-3.5 w-3.5" />
          Выйти
        </button>
      </div>
    </header>
  )
}

export default Topbar
