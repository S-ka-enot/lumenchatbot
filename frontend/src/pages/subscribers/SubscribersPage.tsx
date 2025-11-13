import { useEffect, useRef, useState } from 'react'

import type { SubscriberListItem } from '@/lib/api'
import {
  useCreateSubscriberMutation,
  useExtendSubscriptionMutation,
  useUpdateSubscriberMutation,
  useDeleteSubscriberMutation,
  useCancelSubscriptionMutation,
} from '@/hooks/api/useSubscriberMutations'
import { getAxiosErrorMessage } from '@/hooks/api/utils'
import { useSubscribers } from '@/hooks/api/useSubscribers'
import { subscribersApi } from '@/lib/api'

import ExtendSubscriptionModal, {
  type ExtendSubscriptionValues,
} from '@/components/subscribers/ExtendSubscriptionModal'
import SubscriberFormModal, {
  type SubscriberFormValues,
} from '@/components/subscribers/SubscriberFormModal'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'

const statusStyles: Record<
  string,
  {
    label: string
    className: string
  }
> = {
  active: { label: 'Активна', className: 'bg-emerald-100 text-emerald-600' },
  pending: { label: 'Требует оплаты', className: 'bg-amber-100 text-amber-600' },
  expired: { label: 'Истекла', className: 'bg-rose-100 text-rose-600' },
  inactive: { label: 'Нет подписки', className: 'bg-slate-200 text-slate-600' },
  blocked: { label: 'Заблокирована', className: 'bg-rose-200 text-rose-700' },
}

const SubscribersPage = () => {
  const [page, setPage] = useState(1)
  const [size] = useState(50)
  const { data, isLoading, isError, refetch } = useSubscribers(page, size)
  const subscribers = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / size)

  const createMutation = useCreateSubscriberMutation()
  const updateMutation = useUpdateSubscriberMutation()
  const extendMutation = useExtendSubscriptionMutation()
  const deleteMutation = useDeleteSubscriberMutation()
  const cancelSubscriptionMutation = useCancelSubscriptionMutation()

  const [formOpen, setFormOpen] = useState(false)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [activeSubscriber, setActiveSubscriber] = useState<SubscriberListItem | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const [extendOpen, setExtendOpen] = useState(false)
  const [extendSubscriber, setExtendSubscriber] = useState<SubscriberListItem | null>(null)
  const [extendError, setExtendError] = useState<string | null>(null)

  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(
    null
  )
  const alertTimerRef = useRef<number | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const showAlert = (message: string, type: 'success' | 'error' = 'success') => {
    if (alertTimerRef.current) {
      window.clearTimeout(alertTimerRef.current)
    }
    setAlert({ message, type })
    alertTimerRef.current = window.setTimeout(() => {
      setAlert(null)
      alertTimerRef.current = null
    }, type === 'success' ? 3500 : 5000)
  }

  useEffect(() => {
    return () => {
      if (alertTimerRef.current) {
        window.clearTimeout(alertTimerRef.current)
      }
    }
  }, [])

  const openCreateModal = () => {
    setFormMode('create')
    setActiveSubscriber(null)
    setFormError(null)
    setFormOpen(true)
  }

  const openEditModal = (subscriber: SubscriberListItem) => {
    setFormMode('edit')
    setActiveSubscriber(subscriber)
    setFormError(null)
    setFormOpen(true)
  }

  const openExtendModal = (subscriber: SubscriberListItem) => {
    setExtendSubscriber(subscriber)
    setExtendError(null)
    setExtendOpen(true)
  }

  const closeFormModal = () => {
    setFormOpen(false)
    setFormError(null)
    setActiveSubscriber(null)
  }

  const closeExtendModal = () => {
    setExtendOpen(false)
    setExtendError(null)
    setExtendSubscriber(null)
  }

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const blob = await subscribersApi.export()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `subscribers-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      showAlert('Экспорт завершён — файл сохранён')
    } catch (error) {
      showAlert(getAxiosErrorMessage(error, 'Не удалось выполнить экспорт'), 'error')
    } finally {
      setIsExporting(false)
    }
  }

  const handleCreate = async (values: SubscriberFormValues) => {
    setFormError(null)
    try {
      await createMutation.mutateAsync({
        bot_id: values.botId ? Number(values.botId) : undefined,
        telegram_id: Number(values.telegramId),
        username: values.username || undefined,
        first_name: values.firstName || undefined,
        last_name: values.lastName || undefined,
        phone_number: values.phoneNumber || undefined,
        is_blocked: values.isBlocked,
        subscription_days: values.subscriptionDays ? Number(values.subscriptionDays) : undefined,
        subscription_amount: values.subscriptionAmount || undefined,
        subscription_description: values.subscriptionDescription || undefined,
      })
      closeFormModal()
      showAlert('Участница успешно добавлена')
    } catch (error) {
      setFormError(getAxiosErrorMessage(error, 'Не удалось добавить участницу'))
      throw error
    }
  }

  const handleUpdate = async (values: SubscriberFormValues) => {
    if (!activeSubscriber) return
    setFormError(null)
    try {
      await updateMutation.mutateAsync({
        subscriberId: activeSubscriber.id,
        payload: {
          username: values.username || undefined,
          first_name: values.firstName || undefined,
          last_name: values.lastName || undefined,
          phone_number: values.phoneNumber || undefined,
          is_blocked: values.isBlocked,
        },
      })
      closeFormModal()
      showAlert('Изменения сохранены')
    } catch (error) {
      setFormError(getAxiosErrorMessage(error, 'Не удалось сохранить изменения'))
      throw error
    }
  }

  const handleExtend = async (values: ExtendSubscriptionValues) => {
    if (!extendSubscriber) return
    setExtendError(null)
    try {
      await extendMutation.mutateAsync({
        subscriberId: extendSubscriber.id,
        payload: {
          days: Number(values.days) || 0,
          amount: values.amount || undefined,
          description: values.description || undefined,
        },
      })
      closeExtendModal()
      showAlert('Подписка успешно продлена')
    } catch (error) {
      setExtendError(getAxiosErrorMessage(error, 'Не удалось продлить подписку'))
      throw error
    }
  }

  const handleCancelSubscription = async (subscriber: SubscriberListItem) => {
    if (!subscriber.active_subscription_id) {
      return
    }
    if (
      !window.confirm(
        `Отключить доступ для «${subscriber.full_name}»? Подписка будет завершена немедленно.`
      )
    ) {
      return
    }
    try {
      await cancelSubscriptionMutation.mutateAsync({
        subscriberId: subscriber.id,
        subscriptionId: subscriber.active_subscription_id,
      })
      showAlert('Подписка отключена')
    } catch (error) {
      showAlert(getAxiosErrorMessage(error, 'Не удалось отключить подписку'), 'error')
    }
  }

  const handleDeleteSubscriber = async (subscriber: SubscriberListItem) => {
    if (
      !window.confirm(
        `Удалить участницу «${subscriber.full_name}» совсем? Эта операция необратима.`
      )
    ) {
      return
    }
    try {
      await deleteMutation.mutateAsync(subscriber.id)
      showAlert('Участница удалена')
    } catch (error) {
      showAlert(getAxiosErrorMessage(error, 'Не удалось удалить участницу'), 'error')
    }
  }

  const isMutating =
    createMutation.isPending ||
    updateMutation.isPending ||
    extendMutation.isPending ||
    deleteMutation.isPending ||
    cancelSubscriptionMutation.isPending

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Участницы клуба</h1>
        <p className="text-sm text-slate-500">
          Управляйте профилями, продлевайте подписки и отслеживайте активность участниц.
        </p>
      </header>

      {alert ? (
        <div
          className={`rounded-lg px-4 py-3 text-sm ${
            alert.type === 'success'
              ? 'border border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border border-rose-200 bg-rose-50 text-rose-600'
          }`}
        >
          {alert.message}
        </div>
      ) : null}

      <SubscriberFormModal
        open={formOpen}
        mode={formMode}
        initialData={activeSubscriber ?? undefined}
        onClose={closeFormModal}
        onSubmit={formMode === 'create' ? handleCreate : handleUpdate}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
        error={formError}
      />

      <ExtendSubscriptionModal
        open={extendOpen}
        onClose={closeExtendModal}
        onSubmit={handleExtend}
        isSubmitting={extendMutation.isPending}
        error={extendError}
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-3 border-b border-slate-200 px-6 py-4 md:flex-row md:items-center md:justify-between">
            <input
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400 md:w-72"
              placeholder="Поиск по имени или номеру телефона (скоро)"
              disabled
            />
            <div className="flex items-center gap-2">
              <button
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                onClick={handleExport}
                disabled={isExporting}
              >
                {isExporting ? 'Экспортируем…' : 'Экспорт CSV'}
              </button>
              <button
                className="rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                onClick={openCreateModal}
                disabled={isMutating}
              >
                Добавить участницу
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="space-y-3 p-6">
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-12 w-full rounded-lg" />
            </div>
          ) : subscribers.length === 0 ? (
            <div className="px-6 py-16 text-center text-sm text-slate-500">
              Пока нет участниц в базе. Добавьте первую через кнопку «Добавить участницу».
            </div>
          ) : (
            <table className="w-full border-separate border-spacing-0 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-3">Имя</th>
                  <th className="px-6 py-3">Телефон</th>
                  <th className="px-6 py-3">Тариф</th>
                  <th className="px-6 py-3">Дата окончания</th>
                  <th className="px-6 py-3">Статус</th>
                  <th className="px-6 py-3 text-right">Действия</th>
                </tr>
              </thead>
              <tbody>
                {subscribers.map((subscriber) => {
                  const status =
                    statusStyles[subscriber.status] ?? {
                      label: subscriber.status,
                      className: 'bg-slate-200 text-slate-600',
                    }
                  const formattedExpiresAt = subscriber.expires_at
                    ? new Date(subscriber.expires_at).toLocaleDateString('ru-RU')
                    : '—'

                  return (
                    <tr key={subscriber.id} className="border-b border-slate-100 text-sm">
                      <td className="px-6 py-4 font-medium text-slate-900">
                        {subscriber.full_name}
                        {subscriber.username ? (
                          <span className="block text-xs text-slate-500">@{subscriber.username}</span>
                        ) : null}
                      </td>
                      <td className="px-6 py-4 text-slate-600">
                        {subscriber.phone_number ? subscriber.phone_number : '—'}
                      </td>
                      <td className="px-6 py-4 text-slate-600">{subscriber.tariff ?? '—'}</td>
                      <td className="px-6 py-4 text-slate-600">{formattedExpiresAt}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${status.className}`}
                        >
                          {status.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-60"
                            onClick={() => openEditModal(subscriber)}
                            disabled={isMutating}
                          >
                            Редактировать
                          </button>
                          <button
                            type="button"
                            className="rounded-lg border border-primary-200 px-3 py-1.5 text-xs font-medium text-primary-600 hover:bg-primary-50 disabled:opacity-60"
                            onClick={() => openExtendModal(subscriber)}
                            disabled={isMutating}
                          >
                            Продлить
                          </button>
                          <button
                            type="button"
                            className="rounded-lg border border-amber-200 px-3 py-1.5 text-xs font-medium text-amber-600 hover:bg-amber-50 disabled:opacity-60"
                            onClick={() => handleCancelSubscription(subscriber)}
                            disabled={
                              isMutating || !subscriber.active_subscription_id
                            }
                          >
                            Отключить
                          </button>
                          <button
                            type="button"
                            className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-60"
                            onClick={() => handleDeleteSubscriber(subscriber)}
                            disabled={isMutating}
                          >
                            Удалить
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-200 px-6 py-4">
              <div className="text-sm text-slate-600">
                Показано {subscribers.length} из {total}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1 || isLoading}
                >
                  Назад
                </button>
                <span className="text-sm text-slate-600">
                  Страница {page} из {totalPages}
                </span>
                <button
                  type="button"
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || isLoading}
                >
                  Вперёд
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SubscribersPage



