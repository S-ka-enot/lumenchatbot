import { NAVIGATION, type NavigationSection, type NavigationItem } from '@/lib/navigation'
import { cn } from '@/lib/utils'
import { NavLink } from 'react-router-dom'

const Sidebar = () => {
  return (
    <aside className="flex h-full w-72 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 items-center gap-2 border-b border-slate-200 px-6">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-100 text-primary-600">
          LP
        </span>
        <div>
          <p className="text-sm font-semibold text-slate-900">LumenPay Bot</p>
          <p className="text-xs text-slate-500">Администрирование клуба</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-6">
          {NAVIGATION.map((section: NavigationSection) => (
            <li key={section.title}>
              <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                {section.title}
              </p>
              <ul className="space-y-1">
                {section.items.map((item: NavigationItem) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === '/'}
                      className={({ isActive }) =>
                        cn(
                          'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100',
                          isActive && 'bg-primary-50 text-primary-600 hover:bg-primary-100'
                        )
                      }
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.badge ? (
                        <span className="rounded-full bg-primary-100 px-2 py-0.5 text-xs text-primary-600">
                          {item.badge}
                        </span>
                      ) : null}
                    </NavLink>
                    {item.description ? (
                      <p className="px-3 text-xs text-slate-400">{item.description}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-slate-200 px-6 py-4">
        <div className="rounded-lg bg-slate-100 p-3 text-xs text-slate-600">
          <p className="font-semibold text-slate-700">Онбординг</p>
          <p className="mt-1">
            Добавьте токен бота и ключ YooKassa, чтобы начать продажи подписок.
          </p>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar



