import { useState } from 'react'

import PromoCodeEditModal from '@/components/promocodes/PromoCodeEditModal'
import { useCreatePromoCode, usePromoCodes, useUpdatePromoCode } from '@/hooks/api/usePromoCodes'
import type { PromoCode, PromoCodeCreatePayload } from '@/lib/api'

const PromoCodesPage = () => {
  const { data: promoCodes = [], isLoading } = usePromoCodes()
  const createMutation = useCreatePromoCode()
  const updateMutation = useUpdatePromoCode()

  const [selectedPromo, setSelectedPromo] = useState<PromoCode | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)

  const openModal = (promo: PromoCode) => {
    setSelectedPromo(promo)
    setIsModalOpen(true)
  }

  const handleSubmit = async (promo: PromoCode | PromoCodeCreatePayload) => {
    try {
      if ('id' in promo && promo.id) {
        // Обновление
        await updateMutation.mutateAsync({
          id: promo.id,
          payload: {
            discount_type: promo.discount_type,
            discount_value: promo.discount_value,
            max_uses: promo.max_uses,
            valid_from: promo.valid_from,
            valid_until: promo.valid_until,
            description: promo.description,
            is_active: promo.is_active,
          },
        })
    setFeedback('Промокод обновлён')
      } else {
        // Создание
        await createMutation.mutateAsync({
          bot_id: promo.bot_id,
          code: promo.code,
          discount_type: promo.discount_type,
          discount_value: promo.discount_value,
          max_uses: promo.max_uses,
          valid_from: promo.valid_from,
          valid_until: promo.valid_until,
          description: promo.description,
        })
        setFeedback('Промокод создан')
      }
    window.setTimeout(() => setFeedback(null), 3500)
    setIsModalOpen(false)
    setSelectedPromo(null)
    } catch (error) {
      setFeedback(`Ошибка: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
      window.setTimeout(() => setFeedback(null), 5000)
    }
  }

  const handleCreate = () => {
    // Для создания нужен bot_id, но пока используем первый доступный бот
    // В будущем можно добавить выбор бота
    const newPromo: Partial<PromoCode> = {
      bot_id: promoCodes[0]?.bot_id || 1,
      code: 'NEWCODE',
      discount_type: 'percentage',
      discount_value: '10',
      max_uses: 100,
      valid_until: null,
      description: null,
      is_active: true,
    }
    setSelectedPromo(newPromo as PromoCode)
    setIsModalOpen(true)
    setFeedback('Создан новый промокод — обновите параметры перед запуском')
    window.setTimeout(() => setFeedback(null), 3500)
  }

  const handleDeactivate = async (promo: PromoCode) => {
    try {
      await updateMutation.mutateAsync({
        id: promo.id,
        payload: { is_active: false },
      })
      setFeedback(`Промокод ${promo.code} деактивирован`)
    window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      setFeedback(`Ошибка: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`)
      window.setTimeout(() => setFeedback(null), 5000)
    }
  }

  const formatDiscount = (promo: PromoCode): string => {
    if (promo.discount_type === 'percentage') {
      return `${promo.discount_value}%`
    }
    return `${promo.discount_value} ${promo.discount_type === 'fixed' ? 'RUB' : ''}`
  }

  const formatUsage = (promo: PromoCode): string => {
    if (promo.max_uses === null) {
      return `${promo.used_count} использований`
    }
    return `${promo.used_count} / ${promo.max_uses}`
  }

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return 'Без ограничений'
    try {
      return new Date(dateStr).toLocaleDateString('ru-RU')
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Промокоды и акции</h1>
          <p className="text-sm text-slate-500">Загрузка...</p>
        </header>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Промокоды и акции</h1>
        <p className="text-sm text-slate-500">
          Создавайте временные предложения, отслеживайте эффективность и управление скидками.
        </p>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      <PromoCodeEditModal
        open={isModalOpen}
        promo={selectedPromo}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedPromo(null)
        }}
        onSubmit={handleSubmit}
      />

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <p className="text-sm font-medium text-slate-900">Активные промокоды</p>
            <p className="text-xs text-slate-500">Следите за использованием и сроками действия.</p>
          </div>
          <button
            className="rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-500"
            type="button"
            onClick={handleCreate}
          >
            Создать промокод
          </button>
        </div>
        <div className="grid gap-4 p-6 md:grid-cols-3">
          {promoCodes.length === 0 ? (
            <div className="col-span-3 py-8 text-center text-sm text-slate-500">
              Промокоды не найдены. Создайте первый промокод.
            </div>
          ) : (
            promoCodes.map((promo) => (
              <article
                key={promo.id}
                className={`rounded-lg border p-4 ${
                  promo.is_active
                    ? 'border-slate-200 bg-white'
                    : 'border-slate-100 bg-slate-50 opacity-60'
                }`}
              >
              <p className="text-xs uppercase tracking-wide text-slate-500">Промокод</p>
              <h2 className="mt-2 text-lg font-semibold text-slate-900">{promo.code}</h2>
                <p className="mt-1 text-sm text-slate-600">Скидка: {formatDiscount(promo)}</p>
                <p className="mt-1 text-sm text-slate-600">Использование: {formatUsage(promo)}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Действует до {formatDate(promo.valid_until)}
                </p>
                {promo.description && (
                  <p className="mt-2 text-xs text-slate-500">{promo.description}</p>
                )}
              <div className="mt-4 flex gap-2">
                <button
                  className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100"
                  type="button"
                  onClick={() => openModal(promo)}
                >
                  Редактировать
                </button>
                  {promo.is_active && (
                <button
                  className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-100"
                  type="button"
                  onClick={() => handleDeactivate(promo)}
                >
                  Деактивировать
                </button>
                  )}
              </div>
            </article>
            ))
          )}
        </div>
      </section>
    </div>
  )
}

export default PromoCodesPage
