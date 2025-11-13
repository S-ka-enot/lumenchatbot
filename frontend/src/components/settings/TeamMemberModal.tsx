import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'

type TeamMember = {
  id: string
  name: string
  role: string
  telegram: string
  receivesNotifications: boolean
}

type TeamMemberModalProps = {
  open: boolean
  member: TeamMember | null
  onClose: () => void
  onSubmit: (member: TeamMember) => Promise<void>
}

const roles = ['владелец', 'менеджер', 'аналитик', 'саппорт']

const TeamMemberModal = ({ open, member, onClose, onSubmit }: TeamMemberModalProps) => {
  const [formValues, setFormValues] = useState<TeamMember | null>(member)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    setFormValues(member)
    setError(null)
  }, [open, member])

  if (!formValues) {
    return null
  }

  const handleChange = (field: keyof TeamMember) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormValues((prev) => (prev ? { ...prev, [field]: event.target.value } : prev))
  }

  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target
    setFormValues((prev) => (prev ? { ...prev, receivesNotifications: checked } : prev))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!formValues.name.trim()) {
      setError('Укажите имя участника')
      return
    }
    try {
      await onSubmit(formValues)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Не удалось сохранить участника команды')
      }
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Редактирование участника команды"
      description="Назначьте роль и обновите контактную информацию."
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
              form="team-member-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500"
            >
              Сохранить
            </button>
          </div>
        </div>
      }
    >
      <form id="team-member-form" className="space-y-4" onSubmit={handleSubmit}>
        <label className="block text-xs font-medium text-slate-600">
          Имя и фамилия
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.name}
            onChange={handleChange('name')}
          />
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Роль
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.role}
            onChange={handleChange('role')}
          >
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-xs font-medium text-slate-600">
          Telegram (username или ID)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="@username или 123456789"
            value={formValues.telegram}
            onChange={handleChange('telegram')}
          />
          <span className="mt-1 block text-[11px] text-slate-400">
            Этот контакт будет использоваться для уведомлений и резервных копий.
          </span>
        </label>

        <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
          <input
            type="checkbox"
            checked={formValues.receivesNotifications}
            onChange={handleCheckboxChange}
          />
          Получает уведомления от бота
        </label>
      </form>
    </Modal>
  )
}

export type { TeamMember }
export default TeamMemberModal
