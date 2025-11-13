import axios, { AxiosHeaders } from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_BACKEND_API_URL?.toString() ?? 'http://localhost:8000/api/v1'

let authToken: string | null = null

export const setAuthToken = (token: string | null) => {
  authToken = token
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 15000,
})

apiClient.interceptors.request.use((config) => {
  if (authToken) {
    if (!config.headers) {
      config.headers = new AxiosHeaders()
    }
    if (config.headers instanceof AxiosHeaders) {
      config.headers.set('Authorization', `Bearer ${authToken}`)
    } else {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(config.headers as Record<string, any>).Authorization = `Bearer ${authToken}`
    }
  }
  return config
})

// Обработка 401 Unauthorized - автоматический logout
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Очищаем токен
      setAuthToken(null)
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('lumenpay.auth.token')
        // Перенаправляем на логин только если мы не на странице логина
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export type LoginPayload = {
  username: string
  password: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
}

export type MeResponse = {
  id: number
  username: string
  is_active: boolean
  telegram_id?: number | null
  last_login_at?: string | null
}

export const authApi = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', payload)
    return data
  },

  async me(): Promise<MeResponse> {
    const { data } = await apiClient.get<MeResponse>('/auth/me')
    return data
  },
}

export type SubscriberListItem = {
  id: number
  bot_id: number
  telegram_id: number | null
  username: string | null
  first_name: string | null
  last_name: string | null
  full_name: string
  phone_number: string | null
  tariff: string | null
  expires_at: string | null
  status: string
  is_blocked: boolean
  active_subscription_id?: number | null
}

export type SubscriberCreatePayload = {
  bot_id?: number
  telegram_id: number
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  phone_number?: string | null
  is_blocked?: boolean
  subscription_days?: number | null
  subscription_amount?: string | null
  subscription_description?: string | null
}

export type SubscriberUpdatePayload = {
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  phone_number?: string | null
  is_blocked?: boolean | null
}

export type SubscriptionExtendPayload = {
  days: number
  amount?: string | null
  description?: string | null
}

export type PaymentListItem = {
  id: number
  invoice: string
  member: string
  amount: string
  status: string
  created_at: string
  plan?: string | null
  provider?: string | null
  paid_at?: string | null
}

export type YooKassaSettings = {
  shop_id: string | null
  is_configured: boolean
  has_api_key: boolean
}

export type YooKassaUpdatePayload = {
  shop_id: string
  api_key?: string | null
}

export type Channel = {
  id: number
  bot_id: number
  channel_id: string
  channel_name: string
  channel_username: string | null
  invite_link: string | null
  description: string | null
  is_active: boolean
  requires_subscription: boolean
  member_count: number | null
  created_at: string
  updated_at: string
}

export type ChannelCreatePayload = {
  bot_id: number
  channel_id: string
  channel_name: string
  channel_username?: string | null
  invite_link?: string | null
  description?: string | null
  is_active?: boolean
  requires_subscription?: boolean
  member_count?: number | null
}

export type ChannelUpdatePayload = {
  channel_name?: string | null
  channel_username?: string | null
  invite_link?: string | null
  description?: string | null
  is_active?: boolean | null
  requires_subscription?: boolean | null
  member_count?: number | null
}

export type SubscriptionPlan = {
  id: number
  bot_id: number
  name: string
  slug: string
  description: string | null
  price_amount: string
  price_currency: string
  duration_days: number
  is_active: boolean
  is_recommended: boolean
  channels: Channel[]
  created_at: string
  updated_at: string
}

export type SubscriptionPlanCreatePayload = {
  bot_id: number
  name: string
  slug: string
  description?: string | null
  price_amount: string
  price_currency?: string
  duration_days: number
  is_active?: boolean
  is_recommended?: boolean
  channel_ids?: number[]
}

export type SubscriptionPlanUpdatePayload = {
  name?: string | null
  slug?: string | null
  description?: string | null
  price_amount?: string | null
  price_currency?: string | null
  duration_days?: number | null
  is_active?: boolean | null
  is_recommended?: boolean | null
  channel_ids?: number[] | null
}

export type BotSummary = {
  id: number
  name: string
  slug: string
  is_active: boolean
  has_token: boolean
}

export type BotDetails = {
  id: number
  name: string
  slug: string
  timezone: string
  is_active: boolean
  has_token: boolean
}

export type BotTokenUpdatePayload = {
  token: string
}

export type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  size: number
}

export const subscribersApi = {
  async list(page = 1, size = 50): Promise<PaginatedResponse<SubscriberListItem>> {
    const { data } = await apiClient.get<PaginatedResponse<SubscriberListItem>>(
      '/subscribers',
      { params: { page, size } }
    )
    return data
  },

  async create(payload: SubscriberCreatePayload): Promise<SubscriberListItem> {
    const { data } = await apiClient.post<SubscriberListItem>('/subscribers', payload)
    return data
  },

  async update(
    subscriberId: number,
    payload: SubscriberUpdatePayload
  ): Promise<SubscriberListItem> {
    const { data } = await apiClient.put<SubscriberListItem>(
      `/subscribers/${subscriberId}`,
      payload
    )
    return data
  },

  async extend(
    subscriberId: number,
    payload: SubscriptionExtendPayload
  ): Promise<SubscriberListItem> {
    const { data } = await apiClient.post<SubscriberListItem>(
      `/subscribers/${subscriberId}/extend`,
      payload
    )
    return data
  },

  async remove(subscriberId: number): Promise<void> {
    await apiClient.delete(`/subscribers/${subscriberId}`)
  },

  async cancelSubscription(
    subscriberId: number,
    subscriptionId: number
  ): Promise<SubscriberListItem> {
    const { data } = await apiClient.delete<SubscriberListItem>(
      `/subscribers/${subscriberId}/subscriptions/${subscriptionId}`
    )
    return data
  },

  async export(): Promise<Blob> {
    const response = await apiClient.get<Blob>('/subscribers/export', {
      responseType: 'blob',
    })
    return response.data
  },
}

export const paymentsApi = {
  async list(page = 1, size = 50): Promise<PaginatedResponse<PaymentListItem>> {
    const { data } = await apiClient.get<PaginatedResponse<PaymentListItem>>(
      '/payments',
      { params: { page, size } }
    )
    return data
  },

  async export(): Promise<Blob> {
    const response = await apiClient.get<Blob>('/payments/export', {
      responseType: 'blob',
    })
    return response.data
  },
}

export const settingsApi = {
  async getYooKassa(): Promise<YooKassaSettings> {
    const { data } = await apiClient.get<YooKassaSettings>('/settings/yookassa')
    return data
  },

  async updateYooKassa(payload: YooKassaUpdatePayload): Promise<YooKassaSettings> {
    const { data } = await apiClient.put<YooKassaSettings>('/settings/yookassa', payload)
    return data
  },
}

export const botsApi = {
  async list(): Promise<BotSummary[]> {
    const { data } = await apiClient.get<BotSummary[]>('/bots')
    return data
  },

  async get(botId: number): Promise<BotDetails> {
    const { data } = await apiClient.get<BotDetails>(`/bots/${botId}`)
    return data
  },

  async updateToken(botId: number, payload: BotTokenUpdatePayload): Promise<BotDetails> {
    const { data } = await apiClient.put<BotDetails>(`/bots/${botId}/token`, payload)
    return data
  },
}

export const channelsApi = {
  async list(
    page = 1,
    size = 50,
    botId?: number
  ): Promise<PaginatedResponse<Channel>> {
    const params: Record<string, unknown> = { page, size }
    if (botId !== undefined) {
      params.bot_id = botId
    }
    const { data } = await apiClient.get<PaginatedResponse<Channel>>('/channels', {
      params,
    })
    return data
  },

  async create(payload: ChannelCreatePayload): Promise<Channel> {
    const { data } = await apiClient.post<Channel>('/channels', payload)
    return data
  },

  async update(channelId: number, payload: ChannelUpdatePayload): Promise<Channel> {
    const { data } = await apiClient.put<Channel>(`/channels/${channelId}`, payload)
    return data
  },

  async remove(channelId: number): Promise<void> {
    await apiClient.delete(`/channels/${channelId}`)
  },
}

export const plansApi = {
  async list(): Promise<SubscriptionPlan[]> {
    const { data } = await apiClient.get<SubscriptionPlan[]>('/plans')
    return data
  },

  async create(payload: SubscriptionPlanCreatePayload): Promise<SubscriptionPlan> {
    const { data } = await apiClient.post<SubscriptionPlan>('/plans', {
      ...payload,
      price_currency: payload.price_currency ?? 'RUB',
    })
    return data
  },

  async update(
    planId: number,
    payload: SubscriptionPlanUpdatePayload
  ): Promise<SubscriptionPlan> {
    const { data } = await apiClient.put<SubscriptionPlan>(`/plans/${planId}`, payload)
    return data
  },

  async remove(planId: number): Promise<void> {
    await apiClient.delete(`/plans/${planId}`)
  },
}

export type PromoCode = {
  id: number
  bot_id: number
  code: string
  discount_type: 'percentage' | 'fixed'
  discount_value: string
  max_uses: number | null
  used_count: number
  is_active: boolean
  valid_from: string | null
  valid_until: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export type PromoCodeCreatePayload = {
  bot_id: number
  code: string
  discount_type: 'percentage' | 'fixed'
  discount_value: string
  max_uses?: number | null
  valid_from?: string | null
  valid_until?: string | null
  description?: string | null
}

export type PromoCodeUpdatePayload = {
  discount_type?: 'percentage' | 'fixed' | null
  discount_value?: string | null
  max_uses?: number | null
  valid_from?: string | null
  valid_until?: string | null
  is_active?: boolean | null
  description?: string | null
}

export const promoCodesApi = {
  async list(botId?: number): Promise<PromoCode[]> {
    const params: Record<string, unknown> = {}
    if (botId !== undefined) {
      params.bot_id = botId
    }
    const { data } = await apiClient.get<PromoCode[]>('/promo-codes', { params })
    return data
  },

  async get(promoCodeId: number): Promise<PromoCode> {
    const { data } = await apiClient.get<PromoCode>(`/promo-codes/${promoCodeId}`)
    return data
  },

  async create(payload: PromoCodeCreatePayload): Promise<PromoCode> {
    const { data } = await apiClient.post<PromoCode>('/promo-codes', payload)
    return data
  },

  async update(promoCodeId: number, payload: PromoCodeUpdatePayload): Promise<PromoCode> {
    const { data } = await apiClient.put<PromoCode>(`/promo-codes/${promoCodeId}`, payload)
    return data
  },

  async remove(promoCodeId: number): Promise<void> {
    await apiClient.delete(`/promo-codes/${promoCodeId}`)
  },
}

export type Broadcast = {
  id: number
  bot_id: number
  channel_id: number | null
  message_title: string | null
  message_text: string
  parse_mode: string | null
  target_audience: string
  user_ids: number[] | null
  birthday_only: boolean
  media_files: Array<Record<string, unknown>> | null
  scheduled_at: string | null
  sent_at: string | null
  status: string
  stats: Record<string, unknown> | null
  buttons: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export type BroadcastCreatePayload = {
  bot_id: number
  channel_id?: number | null
  message_title?: string | null
  message_text: string
  parse_mode?: string | null
  target_audience: string
  user_ids?: number[] | null
  birthday_only?: boolean
  media_files?: Array<Record<string, unknown>> | null
  scheduled_at?: string | null
  status?: string | null
  buttons?: Record<string, unknown> | null
}

export type BroadcastUpdatePayload = {
  channel_id?: number | null
  message_title?: string | null
  message_text?: string | null
  parse_mode?: string | null
  target_audience?: string | null
  user_ids?: number[] | null
  birthday_only?: boolean | null
  media_files?: Array<Record<string, unknown>> | null
  scheduled_at?: string | null
  status?: string | null
  buttons?: Record<string, unknown> | null
}

export const broadcastsApi = {
  async list(page = 1, size = 50, botId?: number): Promise<PaginatedResponse<Broadcast>> {
    const params: Record<string, unknown> = { page, size }
    if (botId !== undefined) {
      params.bot_id = botId
    }
    const { data } = await apiClient.get<PaginatedResponse<Broadcast>>('/broadcasts', { params })
    return data
  },

  async get(broadcastId: number): Promise<Broadcast> {
    const { data } = await apiClient.get<Broadcast>(`/broadcasts/${broadcastId}`)
    return data
  },

  async create(payload: BroadcastCreatePayload): Promise<Broadcast> {
    const { data } = await apiClient.post<Broadcast>('/broadcasts', payload)
    return data
  },

  async update(broadcastId: number, payload: BroadcastUpdatePayload): Promise<Broadcast> {
    const { data } = await apiClient.put<Broadcast>(`/broadcasts/${broadcastId}`, payload)
    return data
  },

  async remove(broadcastId: number): Promise<void> {
    await apiClient.delete(`/broadcasts/${broadcastId}`)
  },

  async getRecipientsCount(broadcastId: number): Promise<{ count: number }> {
    const { data } = await apiClient.get<{ count: number }>(
      `/broadcasts/${broadcastId}/recipients/count`
    )
    return data
  },

  async sendNow(broadcastId: number): Promise<{ sent: number; failed: number; total: number }> {
    const { data } = await apiClient.post<{ sent: number; failed: number; total: number }>(
      `/broadcasts/${broadcastId}/send`
    )
    return data
  },
}


