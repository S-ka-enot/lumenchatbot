import { useState } from 'react'

import BotTokenModal from '@/components/bots/BotTokenModal'
import ErrorState from '@/components/ui/ErrorState'
import Skeleton from '@/components/ui/Skeleton'
import { useBots, useUpdateBotTokenMutation } from '@/hooks/api/useBots'
import { getAxiosErrorMessage } from '@/hooks/api/utils'
import type { BotSummary } from '@/lib/api'

const BotsPage = () => {
  const { data: bots, isLoading, isError, refetch } = useBots()
  const updateTokenMutation = useUpdateBotTokenMutation()

  const [selectedBot, setSelectedBot] = useState<BotSummary | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [modalError, setModalError] = useState<string | null>(null)

  const closeModal = () => {
    setSelectedBot(null)
    setModalError(null)
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
      closeModal()
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

      <BotTokenModal
        open={Boolean(selectedBot)}
        botName={selectedBot?.name ?? null}
        hasToken={Boolean(selectedBot?.has_token)}
        isSubmitting={updateTokenMutation.isPending}
        onSubmit={handleTokenSubmit}
        onClose={closeModal}
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
          </div>

          {isLoading ? (
            <div className="grid gap-4 p-6 md:grid-cols-2">
              <Skeleton className="h-36 w-full rounded-lg" />
              <Skeleton className="h-36 w-full rounded-lg" />
            </div>
          ) : !bots || bots.length === 0 ? (
            <div className="px-6 py-16 text-center text-sm text-slate-500">
              Боты ещё не настроены. Добавьте запись в базе данных и обновите страницу.
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
                      onClick={() => setSelectedBot(bot)}
                      disabled={updateTokenMutation.isPending}
                    >
                      {bot.has_token ? 'Обновить токен' : 'Добавить токен'}
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

