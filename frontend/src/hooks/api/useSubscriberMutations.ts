import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  subscribersApi,
  type SubscriberCreatePayload,
  type SubscriberUpdatePayload,
  type SubscriptionExtendPayload,
} from '@/lib/api'

import { SUBSCRIBERS_QUERY_KEY } from './useSubscribers'

const DASHBOARD_QUERY_KEY = ['dashboard', 'summary'] as const

export const useCreateSubscriberMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SubscriberCreatePayload) => subscribersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIBERS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY })
    },
  })
}

export const useUpdateSubscriberMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      subscriberId,
      payload,
    }: {
      subscriberId: number
      payload: SubscriberUpdatePayload
    }) => subscribersApi.update(subscriberId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIBERS_QUERY_KEY })
    },
  })
}

export const useExtendSubscriptionMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      subscriberId,
      payload,
    }: {
      subscriberId: number
      payload: SubscriptionExtendPayload
    }) => subscribersApi.extend(subscriberId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIBERS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY })
    },
  })
}

export const useDeleteSubscriberMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (subscriberId: number) => subscribersApi.remove(subscriberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIBERS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY })
    },
  })
}

export const useCancelSubscriptionMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      subscriberId,
      subscriptionId,
    }: {
      subscriberId: number
      subscriptionId: number
    }) => subscribersApi.cancelSubscription(subscriberId, subscriptionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SUBSCRIBERS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: DASHBOARD_QUERY_KEY })
    },
  })
}


