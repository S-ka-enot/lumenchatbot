import { useDashboardSummary } from '@/hooks/api/useDashboardSummary'
import { cn } from '@/lib/utils'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'
import {
  ArrowUpRight,
  CreditCard,
  Gift,
  MessageSquare,
  Ticket,
  Users,
} from 'lucide-react'

const iconMap = {
  users: Users,
  'credit-card': CreditCard,
  'arrow-up-right': ArrowUpRight,
  ticket: Ticket,
} as const

const DashboardPage = () => {
  const {
    data: summary,
    isLoading,
    isError,
    refetch,
  } = useDashboardSummary()

  const metrics = summary?.metrics ?? []
  const recentActivity = summary?.recent_activity ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Дашборд</h1>
        <p className="text-sm text-slate-500">
          Конверсии, активность участниц и статус продаж подписок
        </p>
      </div>

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <>
          <section className="grid gap-4 lg:grid-cols-4">
            {isLoading
              ? Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-32 rounded-xl" />
                ))
              : metrics.map((metric) => {
                  const IconComponent =
                    iconMap[metric.icon as keyof typeof iconMap] ?? Gift
                  return (
                    <div
                      key={metric.id ?? metric.title}
                      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-slate-500">{metric.title}</p>
                        <IconComponent className="h-4 w-4 text-primary-500" />
                      </div>
                      <p className="mt-3 text-2xl font-semibold text-slate-900">
                        {metric.value}
                      </p>
                      <p className="mt-2 text-xs text-slate-500">{metric.change}</p>
                    </div>
                  )
                })}
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    Динамика выручки
                  </p>
                  <p className="text-xs text-slate-500">Суммарный доход по дням</p>
                </div>
                <button className="text-xs font-medium text-primary-600" type="button">
                  Экспорт
                </button>
              </div>
              <div className="mt-6 flex h-48 flex-col justify-between rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-xs text-slate-500">
                <p className="text-slate-600">
                  График появится после подключения аналитики
                </p>
                <ul className="grid grid-cols-2 gap-2">
                  {(summary?.revenue_trend ?? []).map((point) => (
                    <li
                      key={point.date}
                      className="flex items-center justify-between rounded-md bg-white/60 px-3 py-2 text-slate-600"
                    >
                      <span>{point.date}</span>
                      <span className="font-medium">
                        {Number(point.value).toLocaleString('ru-RU')} ₽
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">Лента активности</p>
                <MessageSquare className="h-4 w-4 text-primary-500" />
              </div>
              {isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full rounded-lg" />
                  <Skeleton className="h-16 w-full rounded-lg" />
                  <Skeleton className="h-16 w-full rounded-lg" />
                </div>
              ) : (
                <ul className={cn('space-y-4', recentActivity.length === 0 && 'text-sm')}>
                  {recentActivity.length === 0 ? (
                    <li className="rounded-lg border border-slate-100 p-4 text-slate-500">
                      Новых событий пока нет.
                    </li>
                  ) : (
                    recentActivity.map((item) => (
                      <li key={item.id} className="rounded-lg border border-slate-100 p-3">
                        <p className="text-sm font-medium text-slate-800">{item.title}</p>
                        <p className="text-xs text-slate-500">{item.description}</p>
                        <p className="mt-1 text-xs text-slate-400">
                          {new Date(item.timestamp).toLocaleString('ru-RU')}
                        </p>
                      </li>
                    ))
                  )}
                </ul>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  )
}

export default DashboardPage



