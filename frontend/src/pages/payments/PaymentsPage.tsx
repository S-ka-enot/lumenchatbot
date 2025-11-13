import { useState } from 'react'

import PaymentEditModal from '@/components/payments/PaymentEditModal'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'
import type { PaymentListItem } from '@/lib/api'
import { paymentsApi } from '@/lib/api'
import { usePayments } from '@/hooks/api/usePayments'
import { getAxiosErrorMessage } from '@/hooks/api/utils'

const statusStyles: Record<string, { label: string; className: string }> = {
  succeeded: { label: 'Успешно', className: 'bg-emerald-100 text-emerald-600' },
  pending: { label: 'Ожидает', className: 'bg-amber-100 text-amber-600' },
  canceled: { label: 'Отменён', className: 'bg-rose-100 text-rose-600' },
  failed: { label: 'Ошибка', className: 'bg-rose-200 text-rose-700' },
}

const PaymentsPage = () => {
  const [page, setPage] = useState(1)
  const [size] = useState(50)
  const { data, isLoading, isError, refetch } = usePayments(page, size)
  const rows = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / size)
  const [selectedPayment, setSelectedPayment] = useState<PaymentListItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  const openEditModal = (payment: PaymentListItem) => {
    setSelectedPayment(payment)
    setIsModalOpen(true)
    setError(null)
  }

  const handleSubmit = async ({ status }: { status: string }) => {
    if (!selectedPayment) {
      return
    }
    setIsSubmitting(true)
    setError(null)
    try {
      // TODO: добавить API для обновления статуса платежа
      setFeedback(`Статус платежа будет обновлён после реализации API (текущее значение: ${status})`)
      window.setTimeout(() => setFeedback(null), 3500)
      setIsModalOpen(false)
      setSelectedPayment(null)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Не удалось обновить статус платежа')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleExport = async () => {
    setError(null)
    setFeedback(null)
    setIsExporting(true)
    try {
      const blob = await paymentsApi.export()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `payments-${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      setFeedback('Экспорт платежей завершён')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (exportError) {
      setError(getAxiosErrorMessage(exportError, 'Не удалось экспортировать платежи'))
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Платежи</h1>
        <p className="text-sm text-slate-500">
          Актуальный статус платежей, подтверждения YooKassa и методы оплаты.
        </p>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      <PaymentEditModal
        open={isModalOpen}
        payment={selectedPayment}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedPayment(null)
        }}
        onSubmit={handleSubmit}
        isSubmitting={isSubmitting}
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-3 border-b border-slate-200 px-6 py-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900">Сегодняшние операции</p>
              <p className="text-xs text-slate-500">
                Отслеживайте платежи в реальном времени и следите за отклонениями.
              </p>
            </div>
            <button
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              onClick={handleExport}
              disabled={isExporting}
            >
              {isExporting ? 'Экспортируем…' : 'Экспорт CSV'}
            </button>
          </div>

          {isLoading ? (
            <div className="space-y-3 p-6">
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-12 w-full rounded-lg" />
            </div>
          ) : rows.length === 0 ? (
            <div className="px-6 py-16 text-center text-sm text-slate-500">
              Платежей за выбранный период пока нет.
            </div>
          ) : (
            <table className="w-full border-separate border-spacing-0 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-6 py-3">Платёж</th>
                  <th className="px-6 py-3">Участница</th>
                  <th className="px-6 py-3">Сумма</th>
                  <th className="px-6 py-3">Время</th>
                  <th className="px-6 py-3">Статус</th>
                  <th className="px-6 py-3 text-right">Действия</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((payment) => {
                  const status = statusStyles[payment.status] ?? {
                    label: payment.status,
                    className: 'bg-slate-200 text-slate-600',
                  }
                  const createdAtLabel = payment.created_at
                    ? new Date(payment.created_at).toLocaleString('ru-RU')
                    : '—'

                  return (
                    <tr key={payment.id} className="border-b border-slate-100 text-sm">
                      <td className="px-6 py-4 font-medium text-slate-900">{payment.invoice}</td>
                      <td className="px-6 py-4 text-slate-600">{payment.member}</td>
                      <td className="px-6 py-4 text-slate-600">{payment.amount}</td>
                      <td className="px-6 py-4 text-slate-500">{createdAtLabel}</td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${status.className}`}
                        >
                          {status.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          type="button"
                          className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100"
                          onClick={() => openEditModal(payment)}
                        >
                          Редактировать
                        </button>
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
                Показано {rows.length} из {total}
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

      {error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {error}
        </div>
      ) : null}
    </div>
  )
}

export default PaymentsPage



