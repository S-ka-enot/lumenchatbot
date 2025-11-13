import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'
import type { PromoCode, PromoCodeCreatePayload } from '@/lib/api'

type PromoFormValues = PromoCodeCreatePayload & {
  id?: number
  is_active?: boolean
  used_count?: number
  created_at?: string
  updated_at?: string
}

type PromoCodeEditModalProps = {
  open: boolean
  promo: PromoCode | PromoCodeCreatePayload | null
  onClose: () => void
  onSubmit: (promo: PromoCode | PromoCodeCreatePayload) => Promise<void>
}

const PromoCodeEditModal = ({ open, promo, onClose, onSubmit }: PromoCodeEditModalProps) => {
  const [formValues, setFormValues] = useState<PromoFormValues>({
    bot_id: 0,
    code: '',
    discount_type: 'percentage',
    discount_value: '0',
    max_uses: null,
    valid_from: null,
    valid_until: null,
    description: null,
    is_active: true,
  })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    if (promo) {
      setFormValues({
        bot_id: promo.bot_id,
        code: promo.code,
        discount_type: promo.discount_type,
        discount_value: promo.discount_value || '0',
        max_uses: promo.max_uses ?? null,
        valid_from: promo.valid_from ?? null,
        valid_until: promo.valid_until ?? null,
        description: promo.description ?? null,
        is_active: 'is_active' in promo ? promo.is_active ?? true : true,
        id: 'id' in promo ? promo.id : undefined,
        used_count: 'used_count' in promo ? promo.used_count : undefined,
        created_at: 'created_at' in promo ? promo.created_at : undefined,
        updated_at: 'updated_at' in promo ? promo.updated_at : undefined,
      })
    } else {
      setFormValues({
        bot_id: 0,
        code: '',
        discount_type: 'percentage',
        discount_value: '0',
        max_uses: null,
        valid_from: null,
        valid_until: null,
        description: null,
        is_active: true,
      })
    }
    setError(null)
  }, [open, promo])

  const handleChange = (
    field: keyof PromoFormValues
  ) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { type, value } = event.target
    setFormValues((prev) => {
      if (field === 'max_uses') {
        return { ...prev, [field]: value === '' ? null : parseInt(value, 10) }
      }
      if (field === 'discount_value') {
        return { ...prev, [field]: value }
      }
      if (type === 'number') {
        return { ...prev, [field]: value === '' ? null : Number(value) }
      }
      return { ...prev, [field]: value }
    })
  }

  const handleDateChange = (field: 'valid_from' | 'valid_until') => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value
    setFormValues((prev) => ({
      ...prev,
      [field]: value === '' ? null : value,
    }))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!formValues.code?.trim()) {
      setError('Укажите код промокода')
      return
    }
    if (!formValues.discount_value || parseFloat(formValues.discount_value) <= 0) {
      setError('Укажите значение скидки больше 0')
      return
    }
    if (formValues.discount_type === 'percentage' && parseFloat(formValues.discount_value) > 100) {
      setError('Процентная скидка не может быть больше 100%')
      return
    }
    try {
      const payload: PromoCode | PromoCodeCreatePayload = formValues.id
        ? {
            id: formValues.id,
            bot_id: formValues.bot_id,
            code: formValues.code,
            discount_type: formValues.discount_type,
            discount_value: formValues.discount_value,
            max_uses: formValues.max_uses ?? null,
            valid_from: formValues.valid_from ?? null,
            valid_until: formValues.valid_until ?? null,
            description: formValues.description ?? null,
            is_active: formValues.is_active ?? true,
            used_count: formValues.used_count ?? 0,
            created_at: formValues.created_at ?? new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
        : {
            bot_id: formValues.bot_id,
            code: formValues.code,
            discount_type: formValues.discount_type,
            discount_value: formValues.discount_value,
            max_uses: formValues.max_uses ?? null,
            valid_from: formValues.valid_from ?? null,
            valid_until: formValues.valid_until ?? null,
            description: formValues.description ?? null,
          }

      await onSubmit(payload)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Не удалось сохранить промокод')
      }
    }
  }

  const isEdit = Boolean(formValues.id)

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={isEdit ? `Редактирование промокода ${formValues.code}` : 'Создание промокода'}
      description="Настройте размер скидки, лимит использования и срок действия."
      footer={
        <div className="flex items-center justify-between">
          <div className="text-xs text-rose-600">{error}</div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-slate-100"
            >
              Отмена
            </button>
            <button
              type="submit"
              form="promo-edit-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500"
            >
              Сохранить
            </button>
          </div>
        </div>
      }
    >
      <form id="promo-edit-form" className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Код промокода
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.code || ''}
              onChange={handleChange('code')}
              required
              disabled={isEdit}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Тип скидки
            <select
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.discount_type || 'percentage'}
              onChange={handleChange('discount_type')}
            >
              <option value="percentage">Процентная (%)</option>
              <option value="fixed">Фиксированная (RUB)</option>
            </select>
          </label>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Значение скидки
            <input
              type="number"
              step="0.01"
              min="0"
              max={formValues.discount_type === 'percentage' ? '100' : undefined}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.discount_value || ''}
              onChange={handleChange('discount_value')}
              required
            />
            <span className="mt-1 text-xs text-slate-500">
              {formValues.discount_type === 'percentage' ? 'Процент от цены' : 'Сумма в рублях'}
            </span>
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Максимум использований
            <input
              type="number"
              min="1"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.max_uses === null ? '' : formValues.max_uses}
              onChange={handleChange('max_uses')}
              placeholder="Без ограничений"
            />
          </label>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Действует с
            <input
              type="datetime-local"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={
                formValues.valid_from
                  ? new Date(formValues.valid_from).toISOString().slice(0, 16)
                  : ''
              }
              onChange={handleDateChange('valid_from')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Действует до
            <input
              type="datetime-local"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={
                formValues.valid_until
                  ? new Date(formValues.valid_until).toISOString().slice(0, 16)
                  : ''
              }
              onChange={handleDateChange('valid_until')}
            />
          </label>
        </div>

        <label className="block text-xs font-medium text-slate-600">
          Описание
          <textarea
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.description || ''}
            onChange={handleChange('description')}
            rows={3}
          />
        </label>

        {isEdit && (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={Boolean(formValues.is_active ?? true)}
              onChange={(e) => setFormValues((prev) => ({ ...prev, is_active: e.target.checked }))}
              className="rounded border-slate-300"
            />
            <span className="text-xs font-medium text-slate-600">Активен</span>
          </label>
        )}
      </form>
    </Modal>
  )
}

export default PromoCodeEditModal

