import { useState } from 'react'

import BroadcastEditModal, { type BroadcastInfo } from '@/components/broadcasts/BroadcastEditModal'
import { useBroadcasts, useCreateBroadcastMutation, useDeleteBroadcastMutation, useSendBroadcastNowMutation, useUpdateBroadcastMutation } from '@/hooks/api/useBroadcasts'
import type { Broadcast } from '@/lib/api'

const statusStyles: Record<string, string> = {
  draft: 'bg-slate-200 text-slate-700',
  pending: 'bg-primary-100 text-primary-600',
  sending: 'bg-blue-100 text-blue-600',
  completed: 'bg-emerald-100 text-emerald-600',
  canceled: 'bg-rose-100 text-rose-600',
}

const statusLabels: Record<string, string> = {
  draft: 'Черновик',
  pending: 'Запланировано',
  sending: 'Отправляется',
  completed: 'Отправлено',
  canceled: 'Отменено',
}

const audienceLabels: Record<string, string> = {
  all: 'Все пользователи',
  subscribers: 'Все подписчики',
  active_subscribers: 'Активные подписчики',
  expired_subscribers: 'Истекшие подписки',
  expiring_soon: 'Истекают через 3 дня',
  non_subscribers: 'Без подписки',
  birthday: 'День рождения сегодня',
  custom: 'Выбранные пользователи',
}

const BroadcastsPage = () => {
  const [page, setPage] = useState(1)
  const { data: broadcastsData, isLoading } = useBroadcasts(page, 50)
  const createMutation = useCreateBroadcastMutation()
  const updateMutation = useUpdateBroadcastMutation()
  const deleteMutation = useDeleteBroadcastMutation()
  const sendNowMutation = useSendBroadcastNowMutation()

  const [selectedBroadcast, setSelectedBroadcast] = useState<BroadcastInfo | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)

  const convertBroadcastToInfo = (broadcast: Broadcast): BroadcastInfo => {
    return {
      ...broadcast,
      title: broadcast.message_title || 'Без заголовка',
      sendAt: broadcast.scheduled_at
        ? new Date(broadcast.scheduled_at).toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })
        : 'Не запланировано',
      audience: audienceLabels[broadcast.target_audience] || broadcast.target_audience,
    }
  }

  const openModal = (broadcast?: BroadcastInfo) => {
    if (broadcast) {
    setSelectedBroadcast(broadcast)
    } else {
      setSelectedBroadcast(null)
    }
    setIsModalOpen(true)
  }

  const handleSubmit = async (broadcast: BroadcastInfo) => {
    try {
      if (broadcast.id && broadcast.id > 0) {
        // Обновление существующей рассылки
        await updateMutation.mutateAsync({
          broadcastId: broadcast.id,
          payload: {
            channel_id: broadcast.channel_id,
            message_title: broadcast.message_title,
            message_text: broadcast.message_text,
            parse_mode: broadcast.parse_mode,
            target_audience: broadcast.target_audience,
            user_ids: broadcast.user_ids,
            birthday_only: broadcast.birthday_only,
            media_files: broadcast.media_files,
            scheduled_at: broadcast.scheduled_at,
            status: broadcast.status,
          },
        })
        setFeedback('Рассылка обновлена')
      } else {
        // Создание новой рассылки
        await createMutation.mutateAsync({
          bot_id: broadcast.bot_id,
          channel_id: broadcast.channel_id,
          message_title: broadcast.message_title,
          message_text: broadcast.message_text,
          parse_mode: broadcast.parse_mode,
          target_audience: broadcast.target_audience,
          user_ids: broadcast.user_ids,
          birthday_only: broadcast.birthday_only,
          media_files: broadcast.media_files,
          scheduled_at: broadcast.scheduled_at,
          status: broadcast.status || 'draft',
        })
        setFeedback('Рассылка создана')
      }
    window.setTimeout(() => setFeedback(null), 3500)
    setIsModalOpen(false)
    setSelectedBroadcast(null)
    } catch (error) {
      console.error('Ошибка при сохранении рассылки:', error)
      throw error
    }
  }

  const handleCreate = () => {
    openModal()
  }

  const handleDuplicate = async (broadcast: BroadcastInfo) => {
    try {
      await createMutation.mutateAsync({
        bot_id: broadcast.bot_id,
        channel_id: broadcast.channel_id,
        message_title: `${broadcast.message_title || 'Рассылка'} (копия)`,
        message_text: broadcast.message_text,
        parse_mode: broadcast.parse_mode,
        target_audience: broadcast.target_audience,
        user_ids: broadcast.user_ids,
        birthday_only: broadcast.birthday_only,
        media_files: broadcast.media_files,
        scheduled_at: null, // Копия без даты отправки
        status: 'draft',
      })
      setFeedback('Рассылка продублирована — обновите содержание перед отправкой')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      console.error('Ошибка при дублировании рассылки:', error)
      setFeedback('Не удалось продублировать рассылку')
      window.setTimeout(() => setFeedback(null), 3500)
    }
  }

  const handleDelete = async (broadcastId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту рассылку?')) {
      return
    }
    try {
      await deleteMutation.mutateAsync(broadcastId)
      setFeedback('Рассылка удалена')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      console.error('Ошибка при удалении рассылки:', error)
      setFeedback('Не удалось удалить рассылку')
      window.setTimeout(() => setFeedback(null), 3500)
    }
  }

  const handleSendNow = async (broadcastId: number) => {
    if (!confirm('Отправить рассылку сейчас? Она будет отправлена всем получателям немедленно.')) {
      return
    }
    try {
      const result = await sendNowMutation.mutateAsync(broadcastId)
      setFeedback(
        `Рассылка отправлена! Отправлено: ${result.sent}, не удалось: ${result.failed} из ${result.total}`
      )
      window.setTimeout(() => setFeedback(null), 5000)
    } catch (error) {
      console.error('Ошибка при отправке рассылки:', error)
      setFeedback('Не удалось отправить рассылку')
    window.setTimeout(() => setFeedback(null), 3500)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Рассылки</h1>
        <p className="text-sm text-slate-500">
          Планируйте автоматические сообщения, напоминания и кампании для участниц.
        </p>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      <BroadcastEditModal
        open={isModalOpen}
        broadcast={selectedBroadcast}
        onClose={() => {
          setIsModalOpen(false)
          setSelectedBroadcast(null)
        }}
        onSubmit={handleSubmit}
      />

      <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <p className="text-sm font-medium text-slate-900">Рассылки</p>
            <p className="text-xs text-slate-500">
              Создавайте цепочки, используйте сегменты и отслеживайте отправку.
            </p>
          </div>
          <button
            className="rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-500"
            type="button"
            onClick={handleCreate}
          >
            Новая рассылка
          </button>
        </div>

        {isLoading ? (
          <div className="px-6 py-8 text-center text-sm text-slate-500">Загрузка...</div>
        ) : broadcastsData?.items.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-slate-500">
            Нет рассылок. Создайте первую рассылку.
          </div>
        ) : (
          <>
        <ul className="divide-y divide-slate-200">
              {broadcastsData?.items.map((broadcast) => {
                const broadcastInfo = convertBroadcastToInfo(broadcast)
                return (
            <li key={broadcast.id} className="px-6 py-4">
              <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-slate-900">{broadcastInfo.title}</p>
                        <p className="text-xs text-slate-500">{broadcastInfo.audience}</p>
                        {broadcast.channel_id && (
                          <p className="text-xs text-slate-400">Канал: {broadcast.channel_id}</p>
                        )}
                        {broadcast.birthday_only && (
                          <p className="text-xs text-blue-500">Только день рождения</p>
                        )}
                </div>
                <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          statusStyles[broadcast.status] || statusStyles.draft
                        }`}
                >
                        {statusLabels[broadcast.status] || broadcast.status}
                </span>
              </div>
              <div className="mt-3 flex justify-between text-xs text-slate-500">
                      <p>Отправка: {broadcastInfo.sendAt}</p>
                <div className="flex gap-2">
                        {broadcast.status !== 'completed' && (
                          <button
                            className="rounded-lg border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700 hover:bg-primary-100"
                            type="button"
                            onClick={() => handleSendNow(broadcast.id)}
                            disabled={sendNowMutation.isPending}
                          >
                            {sendNowMutation.isPending ? 'Отправка...' : 'Отправить сейчас'}
                          </button>
                        )}
                  <button
                    className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                    type="button"
                          onClick={() => openModal(broadcastInfo)}
                  >
                    Редактировать
                  </button>
                  <button
                    className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                    type="button"
                          onClick={() => handleDuplicate(broadcastInfo)}
                  >
                    Продублировать
                  </button>
                        <button
                          className="rounded-lg border border-rose-200 px-3 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50"
                          type="button"
                          onClick={() => handleDelete(broadcast.id)}
                        >
                          Удалить
                        </button>
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
            {broadcastsData && broadcastsData.total > broadcastsData.size && (
              <div className="border-t border-slate-200 px-6 py-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-slate-500">
                    Показано {broadcastsData.items.length} из {broadcastsData.total}
                  </p>
                  <div className="flex gap-2">
                    <button
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-50"
                      type="button"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Назад
                    </button>
                    <button
                      className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-50"
                      type="button"
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page * broadcastsData.size >= broadcastsData.total}
                    >
                      Вперед
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  )
}

export default BroadcastsPage
