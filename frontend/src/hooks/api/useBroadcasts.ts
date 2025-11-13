import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  broadcastsApi,
  type Broadcast,
  type BroadcastCreatePayload,
  type BroadcastUpdatePayload,
  type PaginatedResponse,
} from '@/lib/api'

import { getAxiosErrorMessage } from './utils'

export const BROADCASTS_QUERY_KEY = ['broadcasts'] as const

export const useBroadcasts = (page = 1, size = 50, botId?: number) => {
  return useQuery<PaginatedResponse<Broadcast>>({
    queryKey: [...BROADCASTS_QUERY_KEY, page, size, botId],
    queryFn: () => broadcastsApi.list(page, size, botId),
  })
}

export const useBroadcast = (broadcastId: number) => {
  return useQuery<Broadcast>({
    queryKey: [...BROADCASTS_QUERY_KEY, broadcastId],
    queryFn: () => broadcastsApi.get(broadcastId),
    enabled: !!broadcastId,
  })
}

export const useCreateBroadcastMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: BroadcastCreatePayload) => broadcastsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BROADCASTS_QUERY_KEY })
    },
  })
}

export const useUpdateBroadcastMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      broadcastId,
      payload,
    }: {
      broadcastId: number
      payload: BroadcastUpdatePayload
    }) => broadcastsApi.update(broadcastId, payload),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: BROADCASTS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: [...BROADCASTS_QUERY_KEY, variables.broadcastId] })
    },
  })
}

export const useDeleteBroadcastMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (broadcastId: number) => broadcastsApi.remove(broadcastId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BROADCASTS_QUERY_KEY })
    },
  })
}

export const useBroadcastRecipientsCount = (broadcastId: number) => {
  return useQuery<{ count: number }>({
    queryKey: [...BROADCASTS_QUERY_KEY, broadcastId, 'recipients', 'count'],
    queryFn: () => broadcastsApi.getRecipientsCount(broadcastId),
    enabled: !!broadcastId,
  })
}

export const useSendBroadcastNowMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (broadcastId: number) => broadcastsApi.sendNow(broadcastId),
    onSuccess: (_, broadcastId) => {
      queryClient.invalidateQueries({ queryKey: BROADCASTS_QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: [...BROADCASTS_QUERY_KEY, broadcastId] })
    },
  })
}

export { getAxiosErrorMessage }

