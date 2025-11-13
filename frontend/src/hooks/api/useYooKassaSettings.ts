import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { settingsApi, type YooKassaSettings, type YooKassaUpdatePayload } from '@/lib/api'

const QUERY_KEY = ['settings', 'yookassa'] as const

export const useYooKassaSettings = () => {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async (): Promise<YooKassaSettings> => settingsApi.getYooKassa(),
  })
}

export const useUpdateYooKassaSettingsMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: YooKassaUpdatePayload) => settingsApi.updateYooKassa(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}
