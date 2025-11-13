import { useEffect, useState } from 'react'

import Modal from '@/components/ui/Modal'
import { getAxiosErrorMessage } from '@/hooks/api/utils'

export type BotTokenFormValues = {
  token: string
}

type BotTokenModalProps = {
  open: boolean
  botName: string | null
  hasToken: boolean
  isSubmitting: boolean
  onSubmit: (values: BotTokenFormValues) => Promise<void>
  onClose: () => void
}

const BotTokenModal = ({
  open,
  botName,
  hasToken,
  isSubmitting,
  onSubmit,
  onClose,
}: BotTokenModalProps) => {
  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      setToken('')
      setError(null)
    }
  }, [open])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    if (!token.trim()) {
      setError('Введите токен бота')
      return
    }
    try {
      await onSubmit({ token: token.trim() })
    } catch (submitError) {
      setError(getAxiosErrorMessage(submitError, 'Не удалось сохранить токен'))
    }
  }

  const description = hasToken
    ? 'Токен уже сохранён. Введите новый, чтобы заменить его.'
    : 'Укажите токен, полученный у @BotFather, чтобы активировать этого бота.'

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Токен для ${botName ?? 'бота'}`}
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
              form="bot-token-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Сохраняем…' : 'Сохранить'}
            </button>
          </div>
        </div>
      }
      isLoading={isSubmitting}
    >
      <form id="bot-token-form" className="space-y-4" onSubmit={handleSubmit}>
        <label className="block text-xs font-medium text-slate-600">
          Токен Telegram бота
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            placeholder="1234567890:ABCDEF..."
            value={token}
            onChange={(event) => setToken(event.target.value)}
          />
          <span className="mt-1 block text-[11px] text-slate-400">
            Токен перед сохранением будет зашифрован и не отображается повторно.
          </span>
        </label>
      </form>
    </Modal>
  )
}

export default BotTokenModal
