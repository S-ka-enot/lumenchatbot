import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  botsApi,
  type BotCreatePayload,
  type BotSummary,
  type BotTokenUpdatePayload,
  type BotUpdatePayload,
} from '@/lib/api'

export const BOTS_QUERY_KEY = ['bots'] as const

export const useBots = () => {
  return useQuery<BotSummary[]>({
    queryKey: BOTS_QUERY_KEY,
    queryFn: () => botsApi.list(),
  })
}

export const useCreateBotMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: BotCreatePayload) => botsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY })
    },
  })
}

export const useUpdateBotMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      botId,
      payload,
    }: {
      botId: number
      payload: BotUpdatePayload
    }) => botsApi.update(botId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY })
    },
  })
}

export const useUpdateBotTokenMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      botId,
      payload,
    }: {
      botId: number
      payload: BotTokenUpdatePayload
    }) => botsApi.updateToken(botId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY })
    },
  })
}

export const useDeleteBotMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (botId: number) => botsApi.delete(botId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY })
    },
  })
}
