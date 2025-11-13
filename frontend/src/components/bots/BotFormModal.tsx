import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'
import { getAxiosErrorMessage } from '@/hooks/api/utils'
import type { BotDetails } from '@/lib/api'

export type BotFormValues = {
  name: string
  slug: string
  timezone: string
  is_active: boolean
}

type BotFormModalProps = {
  open: boolean
  mode: 'create' | 'edit'
  bot?: BotDetails | null
  isSubmitting: boolean
  onSubmit: (values: BotFormValues) => Promise<void>
  onClose: () => void
}

const BotFormModal = ({
  open,
  mode,
  bot,
  isSubmitting,
  onSubmit,
  onClose,
}: BotFormModalProps) => {
  const [formData, setFormData] = useState<BotFormValues>({
    name: '',
    slug: '',
    timezone: 'Europe/Moscow',
    is_active: true,
  })
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      if (mode === 'edit' && bot) {
        setFormData({
          name: bot.name,
          slug: bot.slug,
          timezone: bot.timezone,
          is_active: bot.is_active,
        })
      } else {
        setFormData({
          name: '',
          slug: '',
          timezone: 'Europe/Moscow',
          is_active: true,
        })
      }
      setError(null)
    }
  }, [open, mode, bot])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (!formData.name.trim()) {
      setError('Введите название бота')
      return
    }
    if (!formData.slug.trim()) {
      setError('Введите slug бота')
      return
    }

    try {
      await onSubmit(formData)
    } catch (submitError) {
      setError(getAxiosErrorMessage(submitError, 'Не удалось сохранить бота'))
    }
  }

  const title = mode === 'create' ? 'Создать бота' : `Редактировать ${bot?.name ?? 'бота'}`
  const description =
    mode === 'create'
      ? 'Создайте нового бота для управления подписками.'
      : 'Измените параметры бота.'

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
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
              form="bot-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Сохраняем…' : mode === 'create' ? 'Создать' : 'Сохранить'}
            </button>
          </div>
        </div>
      }
      isLoading={isSubmitting}
    >
      <form id="bot-form" className="space-y-4" onSubmit={handleSubmit}>
        <label className="block text-xs font-medium text-slate-600">
          Название бота
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="Например: LumenPay Bot"
            value={formData.name}
            onChange={(event) => setFormData({ ...formData, name: event.target.value })}
            required
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Slug (уникальный идентификатор)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="Например: lumenpay"
            value={formData.slug}
            onChange={(event) => setFormData({ ...formData, slug: event.target.value.toLowerCase().replace(/\s+/g, '-') })}
            required
            disabled={mode === 'edit'}
          />
          <span className="mt-1 block text-[11px] text-slate-400">
            {mode === 'edit' ? 'Slug нельзя изменить после создания.' : 'Только латинские буквы, цифры и дефисы. Нельзя изменить после создания.'}
          </span>
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Часовой пояс
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formData.timezone}
            onChange={(event) => setFormData({ ...formData, timezone: event.target.value })}
          >
            <option value="Europe/Moscow">Europe/Moscow</option>
            <option value="UTC">UTC</option>
            <option value="Europe/Kiev">Europe/Kiev</option>
            <option value="Asia/Almaty">Asia/Almaty</option>
          </select>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.is_active}
            onChange={(event) => setFormData({ ...formData, is_active: event.target.checked })}
            className="h-4 w-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-xs font-medium text-slate-600">Активен</span>
        </label>
      </form>
    </Modal>
  )
}

export default BotFormModal

