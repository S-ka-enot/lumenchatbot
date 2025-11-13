import { useEffect, useMemo, useState } from 'react'

import type { Channel } from '@/lib/api'

import Modal from '@/components/ui/Modal'

export type PlanFormValues = {
  botId: string
  name: string
  slug: string
  description: string
  priceAmount: string
  priceCurrency: string
  durationDays: string
  isActive: boolean
  isRecommended: boolean
  channelIds: string[]
}

type PlanFormModalProps = {
  open: boolean
  mode: 'create' | 'edit'
  initialData?: Partial<PlanFormValues> | null
  channels: Channel[]
  isSubmitting: boolean
  error?: string | null
  onClose: () => void
  onSubmit: (values: PlanFormValues) => Promise<void>
}

const defaultValues: PlanFormValues = {
  botId: '1',
  name: '',
  slug: '',
  description: '',
  priceAmount: '1990',
  priceCurrency: 'RUB',
  durationDays: '30',
  isActive: true,
  isRecommended: false,
  channelIds: [],
}

const PlanFormModal = ({
  open,
  mode,
  initialData,
  channels,
  isSubmitting,
  error,
  onClose,
  onSubmit,
}: PlanFormModalProps) => {
  const [values, setValues] = useState<PlanFormValues>(defaultValues)
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      setValues(defaultValues)
      setLocalError(null)
      return
    }
    setValues({
      ...defaultValues,
      ...initialData,
      botId: initialData?.botId ?? defaultValues.botId,
      name: initialData?.name ?? defaultValues.name,
      slug: initialData?.slug ?? defaultValues.slug,
      description: initialData?.description ?? defaultValues.description,
      priceAmount: initialData?.priceAmount ?? defaultValues.priceAmount,
      priceCurrency: initialData?.priceCurrency ?? defaultValues.priceCurrency,
      durationDays: initialData?.durationDays ?? defaultValues.durationDays,
      isActive: initialData?.isActive ?? defaultValues.isActive,
      isRecommended: initialData?.isRecommended ?? defaultValues.isRecommended,
      channelIds: initialData?.channelIds ?? defaultValues.channelIds,
    })
    setLocalError(null)
  }, [initialData, open])

  const handleChange =
    (field: keyof PlanFormValues) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const target = event.target
      if (target instanceof HTMLInputElement && target.type === 'checkbox') {
        setValues((prev) => ({
          ...prev,
          [field]: target.checked as unknown as PlanFormValues[keyof PlanFormValues],
        }))
        return
      }

      setValues((prev) => ({
        ...prev,
        [field]: target.value as unknown as PlanFormValues[keyof PlanFormValues],
      }))
    }

  const handleChannelToggle = (channelId: string) => () => {
    setValues((prev) => {
      const set = new Set(prev.channelIds)
      if (set.has(channelId)) {
        set.delete(channelId)
      } else {
        set.add(channelId)
      }
      return { ...prev, channelIds: Array.from(set) }
    })
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLocalError(null)

    if (!values.name.trim()) {
      setLocalError('Укажите название тарифа')
      return
    }
    if (!values.slug.trim()) {
      setLocalError('Укажите slug тарифа')
      return
    }
    if (!values.priceAmount.trim()) {
      setLocalError('Укажите стоимость тарифа')
      return
    }
    if (!values.durationDays.trim()) {
      setLocalError('Укажите длительность тарифа в днях')
      return
    }

    try {
      await onSubmit({
        ...values,
        name: values.name.trim(),
        slug: values.slug.trim(),
        description: values.description.trim(),
        priceAmount: values.priceAmount.trim(),
        priceCurrency: values.priceCurrency.trim() || 'RUB',
        durationDays: values.durationDays.trim(),
      })
    } catch (submitError) {
      if (submitError instanceof Error) {
        setLocalError(submitError.message)
      } else {
        setLocalError('Не удалось сохранить тариф')
      }
    }
  }

  const footer = (
    <div className="flex items-center justify-between">
      <div className="text-xs text-rose-600">{error ?? localError}</div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
          disabled={isSubmitting}
        >
          Отмена
        </button>
        <button
          type="submit"
          form="plan-form"
          className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Сохраняем…' : mode === 'create' ? 'Добавить' : 'Сохранить'}
        </button>
      </div>
    </div>
  )

  const sortedChannels = useMemo(
    () => [...channels].sort((a, b) => a.channel_name.localeCompare(b.channel_name)),
    [channels]
  )

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={mode === 'create' ? 'Добавить тариф' : 'Редактировать тариф'}
      description="Укажите параметры подписки и выберите каналы, которые входят в тариф."
      footer={footer}
      isLoading={isSubmitting}
    >
      <form id="plan-form" className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            ID бота
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={values.botId}
              onChange={handleChange('botId')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Slug тарифа
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="premium"
              value={values.slug}
              onChange={handleChange('slug')}
            />
          </label>
        </div>

        <label className="block text-xs font-medium text-slate-600">
          Название
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="Premium"
            value={values.name}
            onChange={handleChange('name')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Описание
          <textarea
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            rows={3}
            placeholder="Что входит в тариф"
            value={values.description}
            onChange={handleChange('description')}
          />
        </label>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <label className="block text-xs font-medium text-slate-600">
            Стоимость
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={values.priceAmount}
              onChange={handleChange('priceAmount')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Валюта
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={values.priceCurrency}
              onChange={handleChange('priceCurrency')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Длительность (дни)
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={values.durationDays}
              onChange={handleChange('durationDays')}
            />
          </label>
        </div>

        <div className="flex flex-col gap-2 pt-2 text-xs font-medium text-slate-600">
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={values.isActive}
              onChange={handleChange('isActive')}
            />
            Тариф активен
          </label>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={values.isRecommended}
              onChange={handleChange('isRecommended')}
            />
            Рекомендовать тариф
          </label>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-medium text-slate-600">Доступные каналы</p>
          <div className="grid gap-2 md:grid-cols-2">
            {sortedChannels.map((channel) => {
              const id = channel.id.toString()
              return (
                <label
                  key={channel.id}
                  className="flex items-start gap-2 rounded-lg border border-slate-200 p-3 text-xs text-slate-600"
                >
                  <input
                    type="checkbox"
                    checked={values.channelIds.includes(id)}
                    onChange={handleChannelToggle(id)}
                  />
                  <div>
                    <p className="font-medium text-slate-900">{channel.channel_name}</p>
                    <p className="text-[11px] text-slate-500">{channel.description ?? '—'}</p>
                  </div>
                </label>
              )
            })}
            {sortedChannels.length === 0 ? (
              <p className="rounded-lg border border-dashed border-slate-200 p-3 text-xs text-slate-500">
                Каналы пока не добавлены. Можно подключить их позже.
              </p>
            ) : null}
          </div>
        </div>
      </form>
    </Modal>
  )
}

export default PlanFormModal

