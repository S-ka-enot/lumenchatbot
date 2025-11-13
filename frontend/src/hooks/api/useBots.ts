import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { botsApi, type BotDetails, type BotSummary, type BotTokenUpdatePayload } from '@/lib/api'

export const BOTS_QUERY_KEY = ['bots'] as const

export const useBots = () => {
  return useQuery<BotSummary[]>({
    queryKey: BOTS_QUERY_KEY,
    queryFn: () => botsApi.list(),
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
    onSuccess: (_data: BotDetails) => {
      queryClient.invalidateQueries({ queryKey: BOTS_QUERY_KEY })
    },
  })
}
