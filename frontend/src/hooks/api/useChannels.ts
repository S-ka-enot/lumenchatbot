import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  channelsApi,
  type Channel,
  type ChannelCreatePayload,
  type ChannelUpdatePayload,
  type PaginatedResponse,
} from '@/lib/api'

import { getAxiosErrorMessage } from './utils'

export const CHANNELS_QUERY_KEY = ['channels'] as const

export const useChannels = (page = 1, size = 50, botId?: number) => {
  return useQuery<PaginatedResponse<Channel>>({
    queryKey: [...CHANNELS_QUERY_KEY, page, size, botId],
    queryFn: () => channelsApi.list(page, size, botId),
  })
}

export const useCreateChannelMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ChannelCreatePayload) => channelsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHANNELS_QUERY_KEY })
    },
  })
}

export const useUpdateChannelMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      channelId,
      payload,
    }: {
      channelId: number
      payload: ChannelUpdatePayload
    }) => channelsApi.update(channelId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHANNELS_QUERY_KEY })
    },
  })
}

export const useDeleteChannelMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (channelId: number) => channelsApi.remove(channelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHANNELS_QUERY_KEY })
    },
  })
}

export { getAxiosErrorMessage }
