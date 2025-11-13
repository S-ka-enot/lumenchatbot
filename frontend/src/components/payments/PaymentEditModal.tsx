import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'
import type { PaymentListItem } from '@/lib/api'

type PaymentEditModalProps = {
  open: boolean
  payment: PaymentListItem | null
  onClose: () => void
  onSubmit: (values: { status: string; note?: string }) => Promise<void>
  isSubmitting?: boolean
}

const PAYMENT_STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: 'succeeded', label: 'Успешно' },
  { value: 'pending', label: 'Ожидает' },
  { value: 'canceled', label: 'Отменён' },
  { value: 'failed', label: 'Ошибка' },
]

const PaymentEditModal = ({ open, payment, onClose, onSubmit, isSubmitting }: PaymentEditModalProps) => {
  const [status, setStatus] = useState<string>('pending')
  const [note, setNote] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setStatus(payment?.status ?? 'pending')
    setNote('')
    setError(null)
  }, [open, payment?.status])

  if (!payment) {
    return null
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    try {
      await onSubmit({ status, note: note.trim() || undefined })
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Не удалось сохранить изменения по платежу')
      }
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Редактирование платежа ${payment.invoice}`}
      description="Обновите статус платежа и добавьте комментарий для истории."
      footer={
        <div className="flex items-center justify-between">
          <div className="text-xs text-rose-600">{error}</div>
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
              form="payment-edit-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Сохраняем…' : 'Сохранить'}
            </button>
          </div>
        </div>
      }
    >
      <form id="payment-edit-form" className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Платёж
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
              value={payment.invoice}
              disabled
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Участница
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500"
              value={payment.member}
              disabled
            />
          </label>
        </div>

        <label className="block text-xs font-medium text-slate-600">
          Статус платежа
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            {PAYMENT_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Комментарий (необязательно)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="Например, уточнить поступление через YooKassa"
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>
      </form>
    </Modal>
  )
}

export default PaymentEditModal
