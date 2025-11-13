import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'

type SubscriptionPlan = {
  id: string
  name: string
  price: string
  duration: string
  benefits: number
}

type SubscriptionEditModalProps = {
  open: boolean
  plan: SubscriptionPlan | null
  onClose: () => void
  onSubmit: (plan: SubscriptionPlan) => Promise<void>
}

const SubscriptionEditModal = ({ open, plan, onClose, onSubmit }: SubscriptionEditModalProps) => {
  const [formValues, setFormValues] = useState<SubscriptionPlan | null>(plan)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setFormValues(plan)
    setError(null)
  }, [open, plan])

  if (!formValues) {
    return null
  }

  const handleChange = (field: keyof SubscriptionPlan) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = field === 'benefits' ? Number(event.target.value) : event.target.value
    setFormValues((prev) => (prev ? { ...prev, [field]: value } : prev))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!formValues.name.trim()) {
      setError('Укажите название тарифа')
      return
    }
    try {
      await onSubmit(formValues)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Не удалось сохранить тариф')
      }
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Редактирование тарифа «${formValues.name}»`}
      description="Измените стоимость, длительность или количество включённых преимуществ."
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
              form="subscription-edit-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500"
            >
              Сохранить
            </button>
          </div>
        </div>
      }
    >
      <form id="subscription-edit-form" className="space-y-4" onSubmit={handleSubmit}>
        <label className="block text-xs font-medium text-slate-600">
          Название тарифа
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.name}
            onChange={handleChange('name')}
          />
        </label>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Стоимость
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.price}
              onChange={handleChange('price')}
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Длительность
            <input
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.duration}
              onChange={handleChange('duration')}
            />
          </label>
        </div>

        <label className="block text-xs font-medium text-slate-600">
          Количество преимуществ
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            type="number"
            min={0}
            value={formValues.benefits}
            onChange={handleChange('benefits')}
          />
        </label>
      </form>
    </Modal>
  )
}

export type { SubscriptionPlan }
export default SubscriptionEditModal
