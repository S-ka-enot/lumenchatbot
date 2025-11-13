import { useState } from 'react'

import BotFormModal, { type BotFormValues } from '@/components/bots/BotFormModal'
import BotTokenModal from '@/components/bots/BotTokenModal'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'
import {
  useBots,
  useCreateBotMutation,
  useUpdateBotMutation,
  useUpdateBotTokenMutation,
  useDeleteBotMutation,
} from '@/hooks/api/useBots'
import { getAxiosErrorMessage } from '@/hooks/api/utils'
import type { BotDetails, BotSummary } from '@/lib/api'

const BotsPage = () => {
  const { data: bots, isLoading, isError, refetch } = useBots()
  const updateTokenMutation = useUpdateBotTokenMutation()
  const createBotMutation = useCreateBotMutation()
  const updateBotMutation = useUpdateBotMutation()
  const deleteBotMutation = useDeleteBotMutation()

  const [selectedBot, setSelectedBot] = useState<BotSummary | null>(null)
  const [selectedBotForEdit, setSelectedBotForEdit] = useState<BotDetails | null>(null)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [isFormModalOpen, setIsFormModalOpen] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [modalError, setModalError] = useState<string | null>(null)

  const closeTokenModal = () => {
    setSelectedBot(null)
    setModalError(null)
  }

  const closeFormModal = () => {
    setSelectedBotForEdit(null)
    setIsFormModalOpen(false)
    setModalError(null)
  }

  const openCreateModal = () => {
    setModalMode('create')
    setSelectedBotForEdit(null)
    setIsFormModalOpen(true)
  }

  const openEditModal = async (bot: BotSummary) => {
    try {
      const botDetails = await import('@/lib/api').then((m) => m.botsApi.get(bot.id))
      setModalMode('edit')
      setSelectedBotForEdit(botDetails)
      setIsFormModalOpen(true)
    } catch (error) {
      setModalError(getAxiosErrorMessage(error, 'Не удалось загрузить данные бота'))
    }
  }

  const handleFormSubmit = async (values: BotFormValues) => {
    setModalError(null)
    try {
      if (modalMode === 'create') {
        await createBotMutation.mutateAsync(values)
        setFeedback('Бот успешно создан')
      } else if (selectedBotForEdit) {
        await updateBotMutation.mutateAsync({
          botId: selectedBotForEdit.id,
          payload: values,
        })
        setFeedback('Бот успешно обновлён')
      }
      window.setTimeout(() => setFeedback(null), 3500)
      closeFormModal()
    } catch (error) {
      setModalError(getAxiosErrorMessage(error, 'Не удалось сохранить бота'))
      throw error
    }
  }

  const handleDelete = async (bot: BotSummary) => {
    if (!window.confirm(`Удалить бота «${bot.name}»? Это действие нельзя отменить.`)) {
      return
    }
    try {
      await deleteBotMutation.mutateAsync(bot.id)
      setFeedback('Бот удалён')
      window.setTimeout(() => setFeedback(null), 3500)
    } catch (error) {
      setModalError(getAxiosErrorMessage(error, 'Не удалось удалить бота'))
    }
  }

  const handleTokenSubmit = async ({ token }: { token: string }) => {
    if (!selectedBot) {
      return
    }
    setModalError(null)
    try {
      await updateTokenMutation.mutateAsync({
        botId: selectedBot.id,
        payload: { token },
      })
      setFeedback(`Токен для ${selectedBot.name} обновлён`)
      window.setTimeout(() => setFeedback(null), 3500)
      closeTokenModal()
    } catch (error) {
      setModalError(getAxiosErrorMessage(error, 'Не удалось сохранить токен'))
      throw error
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Боты</h1>
        <p className="text-sm text-slate-500">
          Управляйте токенами, режимами и интеграцией с Telegram.
        </p>
      </header>

      {feedback ? (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {feedback}
        </div>
      ) : null}

      <BotFormModal
        open={isFormModalOpen}
        mode={modalMode}
        bot={selectedBotForEdit}
        isSubmitting={createBotMutation.isPending || updateBotMutation.isPending}
        onSubmit={handleFormSubmit}
        onClose={closeFormModal}
      />

      <BotTokenModal
        open={Boolean(selectedBot)}
        botName={selectedBot?.name ?? null}
        hasToken={Boolean(selectedBot?.has_token)}
        isSubmitting={updateTokenMutation.isPending}
        onSubmit={handleTokenSubmit}
        onClose={closeTokenModal}
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <div>
              <p className="text-sm font-medium text-slate-900">Список ботов</p>
              <p className="text-xs text-slate-500">
                Подключайте рабочие и тестовые инстансы LumenPay Bot.
              </p>
            </div>
            <button
              type="button"
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-500"
              onClick={openCreateModal}
            >
              Добавить бота
            </button>
          </div>

          {isLoading ? (
            <div className="grid gap-4 p-6 md:grid-cols-2">
              <Skeleton className="h-36 w-full rounded-lg" />
              <Skeleton className="h-36 w-full rounded-lg" />
            </div>
          ) : !bots || bots.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <p className="text-sm text-slate-500 mb-4">
                Боты ещё не настроены. Создайте первого бота, чтобы начать работу.
              </p>
              <button
                type="button"
                className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-500"
                onClick={openCreateModal}
              >
                Создать бота
              </button>
            </div>
          ) : (
            <div className="grid gap-4 p-6 md:grid-cols-2">
              {bots.map((bot) => (
                <article key={bot.id} className="rounded-lg border border-slate-200 p-4">
                  <h2 className="text-lg font-semibold text-slate-900">{bot.name}</h2>
                  <p className="mt-1 text-sm text-slate-500">@{bot.slug}</p>
                  <p className={`mt-3 text-xs font-medium ${bot.is_active ? 'text-emerald-600' : 'text-slate-500'}`}>
                    Статус: {bot.is_active ? 'Активен' : 'Отключён'}
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    Токен: {bot.has_token ? 'сохранён' : 'не задан'}
                  </p>
                  <div className="mt-4 flex gap-2">
                    <button
                      className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-70"
                      type="button"
                      onClick={() => openEditModal(bot)}
                      disabled={updateBotMutation.isPending || deleteBotMutation.isPending}
                    >
                      Редактировать
                    </button>
                    <button
                      className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-70"
                      type="button"
                      onClick={() => setSelectedBot(bot)}
                      disabled={updateTokenMutation.isPending}
                    >
                      {bot.has_token ? 'Токен' : 'Токен'}
                    </button>
                    <button
                      className="rounded-lg border border-rose-200 px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-70"
                      type="button"
                      onClick={() => handleDelete(bot)}
                      disabled={deleteBotMutation.isPending}
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

      {modalError ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {modalError}
        </div>
      ) : null}
    </div>
  )
}

export default BotsPage

