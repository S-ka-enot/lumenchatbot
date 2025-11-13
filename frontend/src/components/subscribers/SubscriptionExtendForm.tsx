import { useEffect, useState } from 'react'

import type { SubscriptionExtendPayload } from '@/lib/api/subscribers'

type SubscriptionExtendFormProps = {
  initialDays?: number
  isSubmitting: boolean
  errorMessage?: string | null
  onSubmit: (payload: SubscriptionExtendPayload) => void
  onCancel: () => void
}

const defaultState = {
  days: '30',
  amount: '',
  description: 'Продление через админку',
}

const SubscriptionExtendForm = ({
  initialDays,
  onSubmit,
  onCancel,
  isSubmitting,
  errorMessage,
}: SubscriptionExtendFormProps) => {
  const [state, setState] = useState(defaultState)

  useEffect(() => {
    setState((prev) => ({
      ...prev,
      days: initialDays ? String(initialDays) : prev.days,
    }))
  }, [initialDays])

  const handleSubmit = () => {
    const payload: SubscriptionExtendPayload = {
      days: Number(state.days),
      amount: state.amount.trim() || undefined,
      description: state.description.trim() || undefined,
    }
    onSubmit(payload)
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault()
        handleSubmit()
      }}
    >
      <label className="flex flex-col gap-1 text-sm">
        Количество дней *
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none"
          type="number"
          min={1}
          max={365}
          required
          value={state.days}
          onChange={(event) => setState((prev) => ({ ...prev, days: event.target.value }))}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Сумма (₽)
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none"
          type="number"
          min={0}
          step="0.01"
          value={state.amount}
          onChange={(event) => setState((prev) => ({ ...prev, amount: event.target.value }))}
          placeholder="Например, 1990"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Описание платежа
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none"
          value={state.description}
          onChange={(event) =>
            setState((prev) => ({ ...prev, description: event.target.value }))
          }
        />
      </label>

      {errorMessage ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-600">
          {errorMessage}
        </p>
      ) : null}

      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
        >
          Отмена
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isSubmitting ? 'Продление...' : 'Продлить'}
        </button>
      </div>
    </form>
  )
}

export default SubscriptionExtendForm


