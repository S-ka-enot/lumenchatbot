import { useEffect, useState } from 'react'

import type { Broadcast, BroadcastCreatePayload } from '@/lib/api'
import { useChannels } from '@/hooks/api/useChannels'
import { useSubscribers } from '@/hooks/api/useSubscribers'
import { useBots } from '@/hooks/api/useBots'

import Modal from '@/components/ui/Modal'

export type BroadcastInfo = Broadcast & {
  title: string
  sendAt: string
  audience: string
}

type BroadcastEditModalProps = {
  open: boolean
  broadcast: BroadcastInfo | null
  onClose: () => void
  onSubmit: (broadcast: BroadcastInfo) => Promise<void>
}

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Черновик' },
  { value: 'pending', label: 'Запланировано' },
  { value: 'sending', label: 'Отправляется' },
  { value: 'completed', label: 'Отправлено' },
  { value: 'canceled', label: 'Отменено' },
]

const AUDIENCE_OPTIONS = [
  { value: 'all', label: 'Все пользователи' },
  { value: 'subscribers', label: 'Все подписчики' },
  { value: 'active_subscribers', label: 'Активные подписчики' },
  { value: 'expired_subscribers', label: 'Истекшие подписки' },
  { value: 'expiring_soon', label: 'Истекают через 3 дня' },
  { value: 'non_subscribers', label: 'Без подписки' },
  { value: 'birthday', label: 'День рождения сегодня' },
  { value: 'custom', label: 'Выбрать пользователей' },
]

const PARSE_MODE_OPTIONS = [
  { value: 'None', label: 'Без форматирования' },
  { value: 'HTML', label: 'HTML' },
  { value: 'Markdown', label: 'Markdown' },
  { value: 'MarkdownV2', label: 'MarkdownV2' },
]

const BroadcastEditModal = ({ open, broadcast, onClose, onSubmit }: BroadcastEditModalProps) => {
  const { data: botsData } = useBots()
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null)
  const { data: channelsData } = useChannels(1, 100, selectedBotId || undefined)
  const { data: subscribersData } = useSubscribers(1, 100)

  const [formValues, setFormValues] = useState<Partial<BroadcastCreatePayload>>({
    bot_id: 0,
    channel_id: null,
    message_title: '',
    message_text: '',
    parse_mode: 'None',
    target_audience: 'all',
    user_ids: [],
    birthday_only: false,
    media_files: [],
    scheduled_at: null,
    status: 'draft',
  })
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([])
  const [mediaFiles, setMediaFiles] = useState<Array<{ type: string; file: File; preview?: string }>>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }
    if (broadcast) {
      setFormValues({
        bot_id: broadcast.bot_id,
        channel_id: broadcast.channel_id,
        message_title: broadcast.message_title || '',
        message_text: broadcast.message_text,
        parse_mode: broadcast.parse_mode || 'None',
        target_audience: broadcast.target_audience,
        user_ids: broadcast.user_ids || [],
        birthday_only: broadcast.birthday_only,
        media_files: broadcast.media_files || [],
        scheduled_at: broadcast.scheduled_at || null,
        status: broadcast.status,
      })
      setSelectedUserIds(broadcast.user_ids || [])
      setSelectedBotId(broadcast.bot_id)
    } else {
      // Новый broadcast
      const firstBot = botsData?.[0]
      if (firstBot) {
        setSelectedBotId(firstBot.id)
        setFormValues({
          bot_id: firstBot.id,
          channel_id: null,
          message_title: '',
          message_text: '',
          parse_mode: 'None',
          target_audience: 'all',
          user_ids: [],
          birthday_only: false,
          media_files: [],
          scheduled_at: null,
          status: 'draft',
        })
      }
    }
    setError(null)
    setMediaFiles([])
  }, [open, broadcast, botsData])

  const handleChange = (field: keyof BroadcastCreatePayload) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const value = event.target.type === 'checkbox' ? (event.target as HTMLInputElement).checked : event.target.value
    setFormValues((prev) => ({ ...prev, [field]: value }))
    if (field === 'bot_id') {
      setSelectedBotId(Number(value))
    }
  }

  const handleUserSelection = (userId: number) => {
    setSelectedUserIds((prev) => {
      if (prev.includes(userId)) {
        return prev.filter((id) => id !== userId)
      }
      return [...prev, userId]
    })
  }

  const handleMediaUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    const newFiles = files.map((file) => ({
      type: file.type.startsWith('image/') ? 'photo' : 'document',
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
    }))
    setMediaFiles((prev) => [...prev, ...newFiles])
  }

  const removeMediaFile = (index: number) => {
    setMediaFiles((prev) => {
      const newFiles = [...prev]
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview!)
      }
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!formValues.message_text?.trim()) {
      setError('Укажите текст сообщения')
      return
    }
    if (formValues.target_audience === 'custom' && selectedUserIds.length === 0) {
      setError('Выберите хотя бы одного пользователя')
      return
    }
    if (!formValues.bot_id) {
      setError('Выберите бота')
      return
    }

    try {
      // Преобразуем медиа файлы в формат для API
      const mediaFilesPayload = mediaFiles.map((mf) => ({
        type: mf.type,
        file_name: mf.file.name,
        file_size: mf.file.size,
        // В реальном приложении здесь будет загрузка файла и получение file_id
        // Пока оставляем заглушку
        file_id: null,
      }))

      const broadcastPayload: BroadcastInfo = {
        ...(broadcast || {}),
        id: broadcast?.id || 0,
        bot_id: formValues.bot_id,
        channel_id: formValues.channel_id || null,
        message_title: formValues.message_title || null,
        message_text: formValues.message_text,
        parse_mode: formValues.parse_mode || 'None',
        target_audience: formValues.target_audience || 'all',
        user_ids: formValues.target_audience === 'custom' ? selectedUserIds : null,
        birthday_only: formValues.birthday_only || false,
        media_files: mediaFilesPayload.length > 0 ? mediaFilesPayload : null,
        scheduled_at: formValues.scheduled_at || null,
        sent_at: broadcast?.sent_at || null,
        status: formValues.status || 'draft',
        stats: broadcast?.stats || null,
        buttons: broadcast?.buttons || null,
        created_at: broadcast?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
        title: formValues.message_title || 'Без заголовка',
        sendAt: formValues.scheduled_at
          ? new Date(formValues.scheduled_at).toLocaleString('ru-RU')
          : 'Не запланировано',
        audience: AUDIENCE_OPTIONS.find((opt) => opt.value === formValues.target_audience)?.label || 'Не указано',
      }

      await onSubmit(broadcastPayload)
    } catch (submitError) {
      if (submitError instanceof Error) {
        setError(submitError.message)
      } else {
        setError('Не удалось сохранить рассылку')
      }
    }
  }

  const formatDateTimeLocal = (dateTime: string | null) => {
    if (!dateTime) return ''
    try {
      const date = new Date(dateTime)
      if (isNaN(date.getTime())) return ''
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day}T${hours}:${minutes}`
    } catch {
      return ''
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={broadcast ? `Редактирование рассылки` : 'Создание новой рассылки'}
      description="Настройте параметры рассылки: выберите канал, аудиторию, составьте сообщение."
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
              form="broadcast-edit-form"
              className="rounded-lg bg-primary-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-primary-500"
            >
              Сохранить
            </button>
          </div>
        </div>
      }
    >
      <form id="broadcast-edit-form" className="space-y-4" onSubmit={handleSubmit}>
        {/* Выбор бота */}
        <label className="block text-xs font-medium text-slate-600">
          Бот
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.bot_id || ''}
            onChange={handleChange('bot_id')}
            required
          >
            <option value="">Выберите бота</option>
            {botsData?.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {bot.name}
              </option>
            ))}
          </select>
        </label>

        {/* Выбор канала */}
        <label className="block text-xs font-medium text-slate-600">
          Канал (опционально)
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.channel_id || ''}
            onChange={(e) => setFormValues((prev) => ({ ...prev, channel_id: e.target.value ? Number(e.target.value) : null }))}
          >
            <option value="">Не выбран</option>
            {channelsData?.items.map((channel) => (
              <option key={channel.id} value={channel.id}>
                {channel.channel_name}
              </option>
            ))}
          </select>
        </label>

        {/* Заголовок сообщения */}
        <label className="block text-xs font-medium text-slate-600">
          Заголовок сообщения (опционально)
          <input
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.message_title || ''}
            onChange={handleChange('message_title')}
            placeholder="Введите заголовок"
          />
        </label>

        {/* Текст сообщения */}
        <label className="block text-xs font-medium text-slate-600">
          Текст сообщения *
          <textarea
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.message_text || ''}
            onChange={handleChange('message_text')}
            rows={6}
            required
            placeholder="Введите текст сообщения"
          />
        </label>

        {/* Форматирование */}
        <label className="block text-xs font-medium text-slate-600">
          Форматирование текста
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.parse_mode || 'None'}
            onChange={handleChange('parse_mode')}
          >
            {PARSE_MODE_OPTIONS.map((mode) => (
              <option key={mode.value} value={mode.value}>
                {mode.label}
              </option>
            ))}
          </select>
        </label>

        {/* Медиа файлы */}
        <label className="block text-xs font-medium text-slate-600">
          Фото / Галерея
          <input
            type="file"
            accept="image/*"
            multiple
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            onChange={handleMediaUpload}
          />
          {mediaFiles.length > 0 && (
            <div className="mt-2 grid grid-cols-3 gap-2">
              {mediaFiles.map((mf, index) => (
                <div key={index} className="relative">
                  {mf.preview ? (
                    <img src={mf.preview} alt={`Preview ${index}`} className="h-20 w-full rounded object-cover" />
                  ) : (
                    <div className="flex h-20 items-center justify-center rounded bg-slate-100 text-xs text-slate-500">
                      {mf.file.name}
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => removeMediaFile(index)}
                    className="absolute right-1 top-1 rounded-full bg-rose-500 p-1 text-xs text-white hover:bg-rose-600"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </label>

        {/* Целевая аудитория */}
        <label className="block text-xs font-medium text-slate-600">
          Целевая аудитория *
          <select
            className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
            value={formValues.target_audience || 'all'}
            onChange={handleChange('target_audience')}
            required
          >
            {AUDIENCE_OPTIONS.map((audience) => (
              <option key={audience.value} value={audience.value}>
                {audience.label}
              </option>
            ))}
          </select>
        </label>

        {/* День рождения */}
        {formValues.target_audience !== 'birthday' && (
          <label className="flex items-center gap-2 text-xs font-medium text-slate-600">
            <input
              type="checkbox"
              checked={formValues.birthday_only || false}
              onChange={(e) => setFormValues((prev) => ({ ...prev, birthday_only: e.target.checked }))}
              className="rounded border-slate-300"
            />
            Только пользователи с днем рождения сегодня
          </label>
        )}

        {/* Выбор пользователей */}
        {formValues.target_audience === 'custom' && (
          <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border border-slate-200 p-3">
            <p className="text-xs font-medium text-slate-600">Выберите пользователей:</p>
            {subscribersData?.items.map((subscriber) => (
              <label key={subscriber.id} className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={selectedUserIds.includes(subscriber.id)}
                  onChange={() => handleUserSelection(subscriber.id)}
                  className="rounded border-slate-300"
                />
                <span>
                  {subscriber.full_name} {subscriber.username ? `(@${subscriber.username})` : ''}
                </span>
              </label>
            ))}
            {selectedUserIds.length > 0 && (
              <p className="text-xs text-slate-500">Выбрано: {selectedUserIds.length}</p>
            )}
          </div>
        )}

        {/* Дата и время отправки */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <label className="block text-xs font-medium text-slate-600">
            Дата и время отправки
            <input
              type="datetime-local"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.scheduled_at ? formatDateTimeLocal(formValues.scheduled_at) : ''}
              onChange={(e) =>
                setFormValues((prev) => ({
                  ...prev,
                  scheduled_at: e.target.value ? new Date(e.target.value).toISOString() : null,
                }))
              }
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            Статус
            <select
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary-400"
              value={formValues.status || 'draft'}
              onChange={handleChange('status')}
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </form>
    </Modal>
  )
}

export default BroadcastEditModal
