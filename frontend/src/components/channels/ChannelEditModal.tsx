import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'

export type ChannelFormValues = {
  botId: string
  channelId: string
  channelName: string
  channelUsername: string
  inviteLink: string
  description: string
  requiresSubscription: boolean
  isActive: boolean
  memberCount: string
}

type ChannelEditModalProps = {
  open: boolean
  mode: 'create' | 'edit'
  initialData?: Partial<ChannelFormValues>
  isSubmitting: boolean
  error?: string | null
  onClose: () => void
  onSubmit: (values: ChannelFormValues) => Promise<void>
}

const defaultValues: ChannelFormValues = {
  botId: '1',
  channelId: '',
  channelName: '',
  channelUsername: '',
  inviteLink: '',
  description: '',
  requiresSubscription: true,
  isActive: true,
  memberCount: '',
}

const ChannelEditModal = ({
  open,
  mode,
  initialData,
  isSubmitting,
  error,
  onClose,
  onSubmit,
}: ChannelEditModalProps) => {
  const [values, setValues] = useState<ChannelFormValues>(defaultValues)
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
      channelId: initialData?.channelId ?? defaultValues.channelId,
      channelName: initialData?.channelName ?? defaultValues.channelName,
      channelUsername: initialData?.channelUsername ?? defaultValues.channelUsername,
      inviteLink: initialData?.inviteLink ?? defaultValues.inviteLink,
      description: initialData?.description ?? defaultValues.description,
      requiresSubscription:
        initialData?.requiresSubscription ?? defaultValues.requiresSubscription,
      isActive: initialData?.isActive ?? defaultValues.isActive,
      memberCount: initialData?.memberCount ?? defaultValues.memberCount,
    })
    setLocalError(null)
  }, [initialData, open])

  const handleChange = (field: keyof ChannelFormValues) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const target = event.target
      const nextValue =
        target instanceof HTMLInputElement && target.type === 'checkbox'
          ? target.checked
          : target.value
      setValues((prev) => ({
        ...prev,
        [field]: nextValue,
      }))
    }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLocalError(null)

    if (!values.channelId.trim()) {
      setLocalError('Укажите ID канала из Telegram')
      return
    }
    if (!values.channelName.trim()) {
      setLocalError('Укажите название канала')
      return
    }

    try {
      await onSubmit(values)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setLocalError(submitError.message)
      } else {
        setLocalError('Не удалось сохранить канал')
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
          form="channel-form"
          className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Сохраняем…' : mode === 'create' ? 'Добавить' : 'Сохранить'}
        </button>
      </div>
    </div>
  )

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={mode === 'create' ? 'Добавить канал' : `Редактировать канал`}
      description="Укажите данные Telegram-канала и права доступа."
      footer={footer}
      isLoading={isSubmitting}
    >
      <form id="channel-form" className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            ID бота
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="1"
              value={values.botId}
              onChange={handleChange('botId')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            ID канала (например, -100123456789)
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="-100..."
              value={values.channelId}
              onChange={handleChange('channelId')}
              disabled={mode === 'edit'}
            />
          </label>
        </div>

        <label className="block text-xs font-medium text-slate-600">
          Название канала
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={values.channelName}
            onChange={handleChange('channelName')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Username (без @)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="lumenclub"
            value={values.channelUsername}
            onChange={handleChange('channelUsername')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Ссылка-приглашение
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="https://t.me/+..."
            type="url"
            value={values.inviteLink}
            onChange={handleChange('inviteLink')}
          />
          <p className="mt-1 text-xs text-slate-400">
            Постоянная ссылка-приглашение для доступа к каналу. Если не указана, бот будет создавать ссылку автоматически.
          </p>
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Описание
          <textarea
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            rows={3}
            placeholder="Используется для доступа по подписке"
            value={values.description}
            onChange={handleChange('description')}
          />
        </label>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Активных участниц (по данным Telegram)
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              type="number"
              min={0}
              value={values.memberCount}
              onChange={handleChange('memberCount')}
            />
          </label>
          <div className="flex flex-col gap-2 pt-6 text-xs font-medium text-slate-600">
            <label className="inline-flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.isActive}
                onChange={handleChange('isActive')}
              />
              Канал активен
            </label>
            <label className="inline-flex items-center gap-2">
              <input
                type="checkbox"
                checked={values.requiresSubscription}
                onChange={handleChange('requiresSubscription')}
              />
              Требуется активная подписка
            </label>
          </div>
        </div>
      </form>
    </Modal>
  )
}

export default ChannelEditModal

