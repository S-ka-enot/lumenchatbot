import { useMemo, useState } from 'react'

import PlanFormModal, {
  type PlanFormValues,
} from '@/components/subscriptions/PlanFormModal'
import Skeleton from '@/components/ui/Skeleton'
import { useChannels } from '@/hooks/api/useChannels'
import {
  useCreatePlanMutation,
  useDeletePlanMutation,
  usePlans,
  useUpdatePlanMutation,
  getAxiosErrorMessage,
} from '@/hooks/api/usePlans'
import type { SubscriptionPlan } from '@/lib/api'

const SubscriptionsPage = () => {
  const plansQuery = usePlans()
  const channelsQuery = useChannels()

  const createPlan = useCreatePlanMutation()
  const updatePlan = useUpdatePlanMutation()
  const deletePlan = useDeletePlanMutation()

  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const openCreateModal = () => {
    setModalMode('create')
    setSelectedPlan(null)
    setIsModalOpen(true)
    setFormError(null)
  }

  const openEditModal = (plan: SubscriptionPlan) => {
    setModalMode('edit')
    setSelectedPlan(plan)
    setIsModalOpen(true)
    setFormError(null)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setSelectedPlan(null)
    setFormError(null)
  }

  const handleSubmit = async (values: PlanFormValues) => {
    setFormError(null)
    const basePayload = {
      bot_id: Number(values.botId) || 1,
      name: values.name.trim(),
      slug: values.slug.trim(),
      description: values.description.trim() || null,
      price_amount: values.priceAmount.trim(),
      price_currency: values.priceCurrency.trim() || 'RUB',
      duration_days: Number(values.durationDays) || 30,
      is_active: values.isActive,
      is_recommended: values.isRecommended,
      channel_ids: values.channelIds.map((id) => Number(id)),
    }

    try {
      const { bot_id, ...planUpdatePayload } = basePayload
      if (modalMode === 'create') {
        await createPlan.mutateAsync(basePayload)
        setFeedback('Тариф успешно создан')
      } else if (selectedPlan) {
        await updatePlan.mutateAsync({
          planId: selectedPlan.id,
          payload: planUpdatePayload,
        })
        setFeedback('Изменения по тарифу сохранены')
      }
      setIsModalOpen(false)
      setSelectedPlan(null)
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      const message = getAxiosErrorMessage(error, 'Не удалось сохранить тариф')
      setFormError(message)
      throw error
    }
  }

  const handleCreatePreset = async (preset: {
    name: string
    slug: string
    description: string
    priceAmount: string
    durationDays: string
    isRecommended: boolean
  }) => {
    setFormError(null)
    try {
      const payload = {
        bot_id: 1,
        name: preset.name,
        slug: preset.slug,
        description: preset.description,
        price_amount: preset.priceAmount,
        price_currency: 'RUB',
        duration_days: Number(preset.durationDays),
        is_active: true,
        is_recommended: preset.isRecommended,
        channel_ids: [],
      }
      await createPlan.mutateAsync(payload)
      setFeedback(`Тариф "${preset.name}" успешно создан`)
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      const message = getAxiosErrorMessage(error, 'Не удалось создать тариф')
      setFormError(message)
    }
  }

  const presetPlans = [
    {
      name: 'Базовый',
      slug: 'basic',
      description: 'Доступ к базовому контенту и основным каналам',
      priceAmount: '990',
      durationDays: '30',
      isRecommended: false,
      color: 'bg-slate-100 text-slate-700',
    },
    {
      name: 'Премиум',
      slug: 'premium',
      description: 'Полный доступ ко всем каналам и эксклюзивному контенту',
      priceAmount: '1990',
      durationDays: '30',
      isRecommended: true,
      color: 'bg-primary-100 text-primary-700',
    },
    {
      name: 'VIP',
      slug: 'vip',
      description: 'Максимальный доступ, персональные консультации и приоритетная поддержка',
      priceAmount: '4990',
      durationDays: '30',
      isRecommended: false,
      color: 'bg-amber-100 text-amber-700',
    },
  ]

  const handleDelete = async (plan: SubscriptionPlan) => {
    if (!window.confirm(`Удалить тариф «${plan.name}»?`)) {
      return
    }
    try {
      await deletePlan.mutateAsync(plan.id)
      setFeedback('Тариф удалён')
      window.setTimeout(() => setFeedback(null), 2500)
    } catch (error) {
      const message = getAxiosErrorMessage(error, 'Не удалось удалить тариф')
      setFeedback(message)
      window.setTimeout(() => setFeedback(null), 3500)
    }
  }

  const plans = plansQuery.data ?? []
  const channels = channelsQuery.data?.items ?? []

  const initialFormValues = useMemo((): Partial<PlanFormValues> | null => {
    if (!selectedPlan) {
      return null
    }
    return {
      botId: selectedPlan.bot_id.toString(),
      name: selectedPlan.name,
      slug: selectedPlan.slug,
      description: selectedPlan.description ?? '',
      priceAmount: selectedPlan.price_amount,
      priceCurrency: selectedPlan.price_currency,
      durationDays: selectedPlan.duration_days.toString(),
      isActive: selectedPlan.is_active,
      isRecommended: selectedPlan.is_recommended,
      channelIds: selectedPlan.channels.map((channel) => channel.id.toString()),
    }
  }, [selectedPlan])

  const isLoading = plansQuery.isLoading || channelsQuery.isLoading
  const isError = plansQuery.isError || channelsQuery.isError

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Подписки</h1>
          <p className="text-sm text-slate-500">
            Управляйте тарифами, стоимостью, длительностью и связанными каналами.
          </p>
        </div>
        <button
          type="button"
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-500"
          onClick={openCreateModal}
        >
          Новый тариф
        </button>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      {isError ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          Не удалось загрузить тарифы. Попробуйте обновить страницу.
        </div>
      ) : null}

      {plans.length === 0 && !isLoading ? (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <h2 className="mb-2 text-lg font-semibold text-slate-900">
              Быстрое создание тарифов
            </h2>
            <p className="mb-4 text-sm text-slate-500">
              Выберите один из готовых вариантов или создайте тариф вручную
            </p>
            <div className="grid gap-4 md:grid-cols-3">
              {presetPlans.map((preset) => (
                <div
                  key={preset.slug}
                  className={`rounded-xl border-2 border-slate-200 p-5 transition hover:border-primary-300 ${preset.color}`}
                >
                  <div className="mb-3 flex items-start justify-between">
                    <h3 className="text-lg font-semibold">{preset.name}</h3>
                    {preset.isRecommended && (
                      <span className="rounded-full bg-primary-600 px-2 py-0.5 text-xs font-medium text-white">
                        Рекомендуется
                      </span>
                    )}
                  </div>
                  <p className="mb-4 text-sm opacity-90">{preset.description}</p>
                  <div className="mb-4 space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="opacity-70">Стоимость:</span>
                      <span className="font-semibold">
                        {Number(preset.priceAmount).toLocaleString('ru-RU')} ₽
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="opacity-70">Длительность:</span>
                      <span className="font-semibold">{preset.durationDays} дней</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCreatePreset(preset)}
                    disabled={createPlan.isPending}
                    className="w-full rounded-lg bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {createPlan.isPending ? 'Создаём...' : 'Создать тариф'}
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500">
            Или нажмите «Новый тариф» выше, чтобы создать тариф с индивидуальными параметрами.
          </div>
        </div>
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-48 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {plans.map((plan) => {
            const channelsList =
              plan.channels.length > 0
                ? plan.channels.map((channel) => channel.channel_name).join(', ')
                : 'Каналы не привязаны'
            return (
              <article
                key={plan.id}
                className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">{plan.name}</h2>
                    <p className="text-xs text-slate-500">Slug: {plan.slug}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2 text-xs">
                    <span
                      className={`rounded-full px-2 py-0.5 ${
                        plan.is_active
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {plan.is_active ? 'Активен' : 'Выключен'}
                    </span>
                    {plan.is_recommended ? (
                      <span className="rounded-full bg-primary-100 px-2 py-0.5 text-primary-600">
                        Рекомендован
                      </span>
                    ) : null}
                  </div>
                </div>

                <p className="mt-4 text-2xl font-semibold text-slate-900">
                  {Number(plan.price_amount).toLocaleString('ru-RU', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{' '}
                  {plan.price_currency}
                </p>
                <p className="text-sm text-slate-500">Длительность: {plan.duration_days} дн.</p>
                {plan.description ? (
                  <p className="mt-2 text-sm text-slate-500">{plan.description}</p>
                ) : null}

                <div className="mt-4 flex-1 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
                  <p className="font-medium text-slate-700">Каналы</p>
                  <p className="mt-1">{channelsList}</p>
                </div>

                <div className="mt-6 flex gap-2">
                  <button
                    className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600 transition hover:bg-slate-100"
                    type="button"
                    onClick={() => openEditModal(plan)}
                  >
                    Редактировать
                  </button>
                  <button
                    className="rounded-lg border border-rose-200 px-3 py-2 text-sm text-rose-600 transition hover:bg-rose-50"
                    type="button"
                    onClick={() => handleDelete(plan)}
                    disabled={deletePlan.isPending}
                  >
                    Удалить
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      )}

      <PlanFormModal
        open={isModalOpen}
        mode={modalMode}
        initialData={initialFormValues ?? undefined}
        channels={channels}
        isSubmitting={createPlan.isPending || updatePlan.isPending}
        error={formError}
        onClose={closeModal}
        onSubmit={handleSubmit}
      />
    </div>
  )
}

export default SubscriptionsPage



