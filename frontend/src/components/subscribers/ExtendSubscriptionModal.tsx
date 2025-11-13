import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'

export type ExtendSubscriptionValues = {
  days: string
  amount: string
  description: string
}

type ExtendSubscriptionModalProps = {
  open: boolean
  onClose: () => void
  onSubmit: (values: ExtendSubscriptionValues) => Promise<void>
  isSubmitting: boolean
  error?: string | null
}

const defaultValues: ExtendSubscriptionValues = {
  days: '30',
  amount: '',
  description: 'Продление через админку',
}

const ExtendSubscriptionModal = ({
  open,
  onClose,
  onSubmit,
  isSubmitting,
  error,
}: ExtendSubscriptionModalProps) => {
  const [values, setValues] = useState<ExtendSubscriptionValues>(defaultValues)
  const [localError, setLocalError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      setValues(defaultValues)
      setLocalError(null)
    }
  }, [open])

  const handleChange = (field: keyof ExtendSubscriptionValues) =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setValues((prev) => ({ ...prev, [field]: event.target.value }))
    }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLocalError(null)

    if (!values.days.trim()) {
      setLocalError('Укажите количество дней продления.')
      return
    }

    try {
      await onSubmit(values)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setLocalError(submitError.message)
      } else {
        setLocalError('Не удалось продлить подписку.')
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
          form="extend-subscription-form"
          className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Продлеваем...' : 'Продлить'}
        </button>
      </div>
    </div>
  )

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Продлить подписку"
      description="Укажите длительность продления и, при необходимости, сумму платежа."
      footer={footer}
    >
      <form id="extend-subscription-form" className="space-y-4" onSubmit={handleSubmit}>
        <label className="block text-xs font-medium text-slate-600">
          Количество дней
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="30"
            value={values.days}
            onChange={handleChange('days')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Сумма платежа, ₽ (необязательно)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="1990"
            value={values.amount}
            onChange={handleChange('amount')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Описание платежа
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="Продление через админку"
            value={values.description}
            onChange={handleChange('description')}
          />
        </label>
      </form>
    </Modal>
  )
}

export default ExtendSubscriptionModal

