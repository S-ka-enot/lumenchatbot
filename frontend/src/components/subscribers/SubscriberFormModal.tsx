import { useEffect, useMemo, useState } from 'react'

import type { SubscriberListItem } from '@/lib/api'

import Modal from '@/components/ui/Modal'

export type SubscriberFormValues = {
  botId: string
  telegramId: string
  username: string
  firstName: string
  lastName: string
  phoneNumber: string
  subscriptionDays: string
  subscriptionAmount: string
  subscriptionDescription: string
  isBlocked: boolean
}

type SubscriberFormModalProps = {
  open: boolean
  mode: 'create' | 'edit'
  initialData?: SubscriberListItem | null
  onClose: () => void
  onSubmit: (values: SubscriberFormValues) => Promise<void>
  isSubmitting: boolean
  isLoading?: boolean
  error?: string | null
}

const defaultValues: SubscriberFormValues = {
  botId: '',
  telegramId: '',
  username: '',
  firstName: '',
  lastName: '',
  phoneNumber: '',
  subscriptionDays: '30',
  subscriptionAmount: '',
  subscriptionDescription: 'Продление через админку',
  isBlocked: false,
}

const SubscriberFormModal = ({
  open,
  mode,
  initialData,
  onClose,
  onSubmit,
  isSubmitting,
  isLoading,
  error,
}: SubscriberFormModalProps) => {
  const [values, setValues] = useState<SubscriberFormValues>(defaultValues)
  const [localError, setLocalError] = useState<string | null>(null)

  const title = useMemo(
    () => (mode === 'create' ? 'Добавить участницу' : 'Редактировать участницу'),
    [mode]
  )

  useEffect(() => {
    if (!open) {
      setValues(defaultValues)
      setLocalError(null)
      return
    }

    if (mode === 'create') {
      setValues({
        ...defaultValues,
        botId: initialData?.bot_id?.toString() ?? '',
      })
      setLocalError(null)
      return
    }

    if (initialData) {
      setValues({
        botId: initialData.bot_id.toString(),
        telegramId: initialData.telegram_id?.toString() ?? '',
        username: initialData.username ?? '',
        firstName: initialData.first_name ?? '',
        lastName: initialData.last_name ?? '',
        phoneNumber: initialData.phone_number ?? '',
        subscriptionDays: '',
        subscriptionAmount: '',
        subscriptionDescription: 'Продление через админку',
        isBlocked: initialData.is_blocked,
      })
    }
  }, [initialData, mode, open])

  const handleChange =
    (field: keyof SubscriberFormValues) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const { value, type, checked } = event.target
      setValues((prev) => ({
        ...prev,
        [field]: type === 'checkbox' ? checked : value,
      }))
    }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLocalError(null)

    if (mode === 'create' && !values.telegramId.trim()) {
      setLocalError('Укажите Telegram ID участницы.')
      return
    }

    try {
      await onSubmit(values)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setLocalError(submitError.message)
      } else {
        setLocalError('Не удалось сохранить изменения.')
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
          form="subscriber-form"
          className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Сохраняем...' : mode === 'create' ? 'Добавить' : 'Сохранить'}
        </button>
      </div>
    </div>
  )

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={
        mode === 'create'
          ? 'Введите данные новой участницы. Telegram ID обязателен.'
          : 'Обновите контактные данные или статус участницы.'
      }
      footer={footer}
      isLoading={isLoading}
    >
      <form id="subscriber-form" className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            ID бота
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="Например, 1"
              value={values.botId}
              onChange={handleChange('botId')}
            />
            <span className="mt-1 block text-[11px] text-slate-400">
              Можно оставить пустым — будет выбран первый доступный бот.
            </span>
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Telegram ID
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="123456789"
              value={values.telegramId}
              onChange={handleChange('telegramId')}
              disabled={mode === 'edit'}
              required={mode === 'create'}
            />
          </label>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Имя
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="Имя"
              value={values.firstName}
              onChange={handleChange('firstName')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Фамилия
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              placeholder="Фамилия"
              value={values.lastName}
              onChange={handleChange('lastName')}
            />
          </label>
        </div>

        <label className="block text-xs font-medium text-slate-600">
          Username (без @)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="username"
            value={values.username}
            onChange={handleChange('username')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Номер телефона
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="+7 ..."
            value={values.phoneNumber}
            onChange={handleChange('phoneNumber')}
          />
        </label>

        <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
          <input
            type="checkbox"
            checked={values.isBlocked}
            onChange={handleChange('isBlocked')}
          />
          Заблокировать участницу
        </label>

        {mode === 'create' ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <label className="block text-xs font-medium text-slate-600">
              Длительность подписки (дни)
              <input
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
                placeholder="30"
                value={values.subscriptionDays}
                onChange={handleChange('subscriptionDays')}
              />
            </label>
            <label className="block text-xs font-medium text-slate-600">
              Сумма платежа, ₽
              <input
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
                placeholder="1990"
                value={values.subscriptionAmount}
                onChange={handleChange('subscriptionAmount')}
              />
            </label>
            <label className="block text-xs font-medium text-slate-600 md:col-span-3">
              Описание платежа
              <input
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
                placeholder="Продление через админку"
                value={values.subscriptionDescription}
                onChange={handleChange('subscriptionDescription')}
              />
            </label>
          </div>
        ) : null}
      </form>
    </Modal>
  )
}

export default SubscriberFormModal

