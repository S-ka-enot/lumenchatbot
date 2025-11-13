import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient, type PromoCode, type PromoCodeCreatePayload, type PromoCodeUpdatePayload } from '@/lib/api'

export const usePromoCodes = (botId?: number) => {
  return useQuery({
    queryKey: ['promoCodes', botId],
    queryFn: async () => {
      const params: Record<string, unknown> = {}
      if (botId !== undefined) {
        params.bot_id = botId
      }
      const { data } = await apiClient.get<PromoCode[]>('/promo-codes', { params })
      return data
    },
  })
}

export const usePromoCode = (promoCodeId: number) => {
  return useQuery({
    queryKey: ['promoCodes', promoCodeId],
    queryFn: async () => {
      const { data } = await apiClient.get<PromoCode>(`/promo-codes/${promoCodeId}`)
      return data
    },
    enabled: !!promoCodeId,
  })
}

export const useCreatePromoCode = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: PromoCodeCreatePayload) => {
      const { data } = await apiClient.post<PromoCode>('/promo-codes', payload)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promoCodes'] })
    },
  })
}

export const useUpdatePromoCode = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: PromoCodeUpdatePayload }) => {
      const { data } = await apiClient.put<PromoCode>(`/promo-codes/${id}`, payload)
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['promoCodes'] })
      queryClient.invalidateQueries({ queryKey: ['promoCodes', variables.id] })
    },
  })
}

export const useDeletePromoCode = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (promoCodeId: number) => {
      await apiClient.delete(`/promo-codes/${promoCodeId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promoCodes'] })
    },
  })
}

