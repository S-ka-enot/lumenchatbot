import { isAxiosError } from 'axios'
import { useEffect, useMemo, useState } from 'react'

import TeamMemberModal, { type TeamMember } from '@/components/settings/TeamMemberModal'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'
import {
  useUpdateYooKassaSettingsMutation,
  useYooKassaSettings,
} from '@/hooks/api/useYooKassaSettings'

const initialMembers: TeamMember[] = [
  {
    id: 'anna',
    name: 'Анна Кузнецова',
    role: 'владелец',
    telegram: '@anna_kuznetsova',
    receivesNotifications: true,
  },
  {
    id: 'maria',
    name: 'Мария Соколова',
    role: 'менеджер',
    telegram: '@maria_sokolova',
    receivesNotifications: false,
  },
]

const SettingsPage = () => {
  const { data: yooKassaSettings, isLoading: isYooKassaLoading, isError: isYooKassaError, refetch: refetchYooKassa } =
    useYooKassaSettings()
  const updateYooKassaMutation = useUpdateYooKassaSettingsMutation()

  const [yooKassaForm, setYooKassaForm] = useState({ shopId: '', apiKey: '' })
  const [yooKassaError, setYooKassaError] = useState<string | null>(null)

  useEffect(() => {
    if (yooKassaSettings) {
      setYooKassaForm((prev) => ({ ...prev, shopId: yooKassaSettings.shop_id ?? '' }))
    }
  }, [yooKassaSettings])

  const handleYooKassaChange = (field: 'shopId' | 'apiKey') =>
    (event: React.ChangeEvent<HTMLInputElement>) => {
      setYooKassaForm((prev) => ({ ...prev, [field]: event.target.value }))
    }

  const handleSaveYooKassa = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setYooKassaError(null)
    try {
      await updateYooKassaMutation.mutateAsync({
        shop_id: yooKassaForm.shopId.trim(),
        api_key: yooKassaForm.apiKey.trim() || undefined,
      })
      setFeedback('Настройки YooKassa сохранены')
      window.setTimeout(() => setFeedback(null), 3500)
      setYooKassaForm((prev) => ({ ...prev, apiKey: '' }))
    } catch (error) {
      if (isAxiosError(error)) {
        const detail = error.response?.data?.detail
        setYooKassaError(typeof detail === 'string' ? detail : 'Не удалось сохранить настройки')
      } else {
        setYooKassaError('Не удалось сохранить настройки')
      }
    }
  }

  const [team, setTeam] = useState<TeamMember[]>(initialMembers)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [selectedMember, setSelectedMember] = useState<TeamMember | null>(null)
  const [isMemberModalOpen, setIsMemberModalOpen] = useState(false)

  const openMemberModal = (member: TeamMember) => {
    setSelectedMember(member)
    setIsMemberModalOpen(true)
  }

  const handleSaveMember = async (member: TeamMember) => {
    setTeam((prev) =>
      prev.map((item) => {
        if (item.id === member.id) {
          return member
        }
        if (member.receivesNotifications) {
          return { ...item, receivesNotifications: false }
        }
        return item
      })
    )
    setFeedback('Настройки участника команды обновлены')
    window.setTimeout(() => setFeedback(null), 3500)
    setIsMemberModalOpen(false)
    setSelectedMember(null)
  }

  const handleAddMember = () => {
    const timestamp = Date.now().toString(36)
    const member: TeamMember = {
      id: `member-${timestamp}`,
      name: 'Новый участник',
      role: 'саппорт',
      telegram: '',
      receivesNotifications: false,
    }
    setTeam((prev) => [member, ...prev])
    setSelectedMember(member)
    setIsMemberModalOpen(true)
  }

  const yooKassaHints = useMemo(() => {
    if (!yooKassaSettings) {
      return null
    }
    if (!yooKassaSettings.has_api_key) {
      return 'API-ключ ещё не указан. Добавьте его для включения YooKassa.'
    }
    if (!yooKassaSettings.is_configured) {
      return 'Shop ID сохранён, но API-ключ отсутствует.'
    }
    return 'API-ключ сохранён. Чтобы обновить значение, введите новый и сохраните.'
  }, [yooKassaSettings])

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Настройки</h1>
        <p className="text-sm text-slate-500">
          Укажите реквизиты YooKassa, управляйте командой и конфигурацией админ-панели.
        </p>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      <TeamMemberModal
        open={isMemberModalOpen}
        member={selectedMember}
        onClose={() => {
          setIsMemberModalOpen(false)
          setSelectedMember(null)
        }}
        onSubmit={handleSaveMember}
      />

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">YooKassa</h2>
          <p className="mt-2 text-xs text-slate-500">
            Добавьте Shop ID и API-ключ, чтобы принимать оплату подписок.
          </p>

          {isYooKassaLoading ? (
            <div className="mt-4 space-y-3">
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-9 w-32 rounded-lg" />
            </div>
          ) : isYooKassaError ? (
            <div className="mt-4">
              <ErrorState onRetry={() => refetchYooKassa()} />
            </div>
          ) : (
            <form className="mt-4 space-y-3 text-sm" onSubmit={handleSaveYooKassa}>
              <label className="block">
                <span className="text-slate-600">Shop ID</span>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
                  placeholder="Например, 123456"
                  type="text"
                  value={yooKassaForm.shopId}
                  onChange={handleYooKassaChange('shopId')}
                />
              </label>
              <label className="block">
                <span className="text-slate-600">API ключ</span>
                <input
                  className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
                  placeholder="Секретный ключ YooKassa"
                  type="password"
                  value={yooKassaForm.apiKey}
                  onChange={handleYooKassaChange('apiKey')}
                />
                {yooKassaHints ? (
                  <span className="mt-1 block text-[11px] text-slate-400">{yooKassaHints}</span>
                ) : null}
              </label>
              {yooKassaError ? (
                <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600">
                  {yooKassaError}
                </div>
              ) : null}
              <button
                className="rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
                type="submit"
                disabled={updateYooKassaMutation.isPending}
              >
                {updateYooKassaMutation.isPending ? 'Сохраняем…' : 'Сохранить'}
              </button>
            </form>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-slate-900">Команда</h2>
          <p className="mt-2 text-xs text-slate-500">Добавьте администраторов и менеджеров.</p>
          <ul className="mt-4 space-y-3 text-sm">
            {team.map((member) => (
              <li
                key={member.id}
                className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2"
              >
                <div>
                  <p className="font-medium text-slate-900">{member.name}</p>
                  <p className="text-xs text-slate-500">Роль: {member.role}</p>
                  <p className="text-xs text-slate-500">
                    Telegram: {member.telegram ? member.telegram : 'не указан'}
                  </p>
                  {member.receivesNotifications ? (
                    <span className="mt-1 inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 text-[11px] font-medium text-primary-600">
                      Получает уведомления
                    </span>
                  ) : null}
                </div>
                <button
                  className="rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-100"
                  type="button"
                  onClick={() => openMemberModal(member)}
                >
                  Настроить
                </button>
              </li>
            ))}
          </ul>
          <button
            className="mt-4 w-full rounded-lg border border-dashed border-primary-300 px-3 py-2 text-xs font-medium text-primary-600 hover:bg-primary-50"
            type="button"
            onClick={handleAddMember}
          >
            Добавить участника команды
          </button>
        </div>
      </section>
    </div>
  )
}

export default SettingsPage

