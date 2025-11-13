import { useState } from 'react'

import ChannelEditModal, { type ChannelFormValues } from '@/components/channels/ChannelEditModal'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'
import {
  useChannels,
  useCreateChannelMutation,
  useDeleteChannelMutation,
  useUpdateChannelMutation,
  getAxiosErrorMessage,
} from '@/hooks/api/useChannels'

const ChannelsPage = () => {
  const { data, isLoading, isError, refetch } = useChannels()
  const createMutation = useCreateChannelMutation()
  const updateMutation = useUpdateChannelMutation()
  const deleteMutation = useDeleteChannelMutation()

  const channels = data?.items ?? []

  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [activeChannel, setActiveChannel] = useState<number | null>(null)
  const [initialValues, setInitialValues] = useState<Partial<ChannelFormValues> | undefined>(
    undefined
  )
  const [modalError, setModalError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const isSubmitting = createMutation.isPending || updateMutation.isPending

  const openCreateModal = () => {
    setModalMode('create')
    setActiveChannel(null)
    setInitialValues(undefined)
    setModalError(null)
    setModalOpen(true)
  }

  const openEditModal = (channelId: number) => {
    const channel = channels.find((item) => item.id === channelId)
    if (!channel) return
    setModalMode('edit')
    setActiveChannel(channelId)
    setInitialValues({
      botId: String(channel.bot_id),
      channelId: channel.channel_id,
      channelName: channel.channel_name,
      channelUsername: channel.channel_username ?? '',
      inviteLink: channel.invite_link ?? '',
      description: channel.description ?? '',
      requiresSubscription: channel.requires_subscription,
      isActive: channel.is_active,
      memberCount: channel.member_count?.toString() ?? '',
    })
    setModalError(null)
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setModalError(null)
    setActiveChannel(null)
  }

  const handleCreate = async (values: ChannelFormValues) => {
    setModalError(null)
    try {
      await createMutation.mutateAsync({
        bot_id: Number(values.botId) || 1,
        channel_id: values.channelId.trim(),
        channel_name: values.channelName.trim(),
        channel_username: values.channelUsername.trim() || null,
        invite_link: values.inviteLink.trim() || null,
        description: values.description.trim() || null,
        requires_subscription: values.requiresSubscription,
        is_active: values.isActive,
        member_count: values.memberCount ? Number(values.memberCount) : null,
      })
      closeModal()
      setFeedback('Канал успешно добавлен')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      const message = getAxiosErrorMessage(error, 'Не удалось добавить канал')
      setModalError(message)
      throw error
    }
  }

  const handleUpdate = async (values: ChannelFormValues) => {
    if (activeChannel === null) return
    setModalError(null)
    try {
      await updateMutation.mutateAsync({
        channelId: activeChannel,
        payload: {
          channel_name: values.channelName.trim() || undefined,
          channel_username: values.channelUsername.trim() || null,
          invite_link: values.inviteLink.trim() || null,
          description: values.description.trim() || null,
          requires_subscription: values.requiresSubscription,
          is_active: values.isActive,
          member_count: values.memberCount ? Number(values.memberCount) : null,
        },
      })
      closeModal()
      setFeedback('Изменения сохранены')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      const message = getAxiosErrorMessage(error, 'Не удалось сохранить канал')
      setModalError(message)
      throw error
    }
  }

  const handleDelete = async (channelId: number) => {
    if (!window.confirm('Удалить канал?')) return
    try {
      await deleteMutation.mutateAsync(channelId)
      setFeedback('Канал удалён')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      setFeedback(getAxiosErrorMessage(error, 'Не удалось удалить канал'))
    }
  }

  const isLoadingState = isLoading || deleteMutation.isPending

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Каналы и чаты</h1>
        <p className="text-sm text-slate-500">
          Управляйте доступом, приглашениями и синхронизацией с Telegram.
        </p>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      <ChannelEditModal
        open={modalOpen}
        mode={modalMode}
        initialData={initialValues}
        isSubmitting={isSubmitting}
        error={modalError}
        onClose={closeModal}
        onSubmit={modalMode === 'create' ? handleCreate : handleUpdate}
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <div>
              <p className="text-sm font-medium text-slate-900">Список каналов</p>
              <p className="text-xs text-slate-500">
                Подключайте новые каналы и отслеживайте статус синхронизации.
              </p>
            </div>
            <button
              className="rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-60"
              type="button"
              onClick={openCreateModal}
              disabled={isSubmitting}
            >
              Подключить канал
            </button>
          </div>

          {isLoadingState ? (
            <div className="grid gap-4 p-6 md:grid-cols-2">
              <Skeleton className="h-36 w-full rounded-lg" />
              <Skeleton className="h-36 w-full rounded-lg" />
            </div>
          ) : channels.length === 0 ? (
            <div className="px-6 py-16 text-center text-sm text-slate-500">
              Каналы ещё не добавлены. Нажмите «Подключить канал», чтобы создать первый.
            </div>
          ) : (
            <div className="grid gap-4 p-6 md:grid-cols-2">
              {channels.map((channel) => (
                <article key={channel.id} className="rounded-lg border border-slate-200 p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-slate-900">{channel.channel_name}</h2>
                      <p className="mt-1 text-sm text-slate-500">
                        {channel.channel_username ? `@${channel.channel_username}` : 'Без username'}
                      </p>
                    </div>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${channel.requires_subscription ? 'bg-primary-100 text-primary-600' : 'bg-slate-200 text-slate-600'}`}
                    >
                      {channel.requires_subscription ? 'По подписке' : 'Открыт'}
                    </span>
                  </div>

                  <p className="mt-3 text-xs text-slate-500">
                    ID: {channel.channel_id} • Участниц: {channel.member_count ?? '—'}
                  </p>
                  {channel.description ? (
                    <p className="mt-2 text-sm text-slate-600">{channel.description}</p>
                  ) : null}

                  <div className="mt-4 flex gap-2">
                    <button
                      className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-60"
                      type="button"
                      onClick={() => openEditModal(channel.id)}
                      disabled={isSubmitting || deleteMutation.isPending}
                    >
                      Настроить
                    </button>
                    <button
                      className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-100 disabled:opacity-60"
                      type="button"
                      onClick={() => handleDelete(channel.id)}
                      disabled={deleteMutation.isPending}
                    >
                      Удалить
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  )
}

export default ChannelsPage

