import { apiClient } from '@/lib/api'

export type SubscriberListItem = {
  id: number
  bot_id: number
  telegram_id?: number | null
  username?: string | null
  first_name?: string | null
  last_name?: string | null
  full_name: string
  phone_number?: string | null
  tariff?: string | null
  expires_at?: string | null
  status: string
  is_blocked: boolean
}

export type SubscriberCreatePayload = {
  bot_id?: number | null
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

export const createSubscriber = async (
  payload: SubscriberCreatePayload,
): Promise<SubscriberListItem> => {
  const { data } = await apiClient.post<SubscriberListItem>('/subscribers', payload)
  return data
}

export const updateSubscriber = async (
  userId: number,
  payload: SubscriberUpdatePayload,
): Promise<SubscriberListItem> => {
  const { data } = await apiClient.put<SubscriberListItem>(
    `/subscribers/${userId}`,
    payload,
  )
  return data
}

export const extendSubscriberSubscription = async (
  userId: number,
  payload: SubscriptionExtendPayload,
): Promise<SubscriberListItem> => {
  const { data } = await apiClient.post<SubscriberListItem>(
    `/subscribers/${userId}/extend`,
    payload,
  )
  return data
}


