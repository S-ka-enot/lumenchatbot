import { useQuery } from '@tanstack/react-query'

import type { PaginatedResponse, PaymentListItem } from '@/lib/api'
import { paymentsApi } from '@/lib/api'

const QUERY_KEY = ['payments', 'list']

export const usePayments = (page = 1, size = 50) => {
  return useQuery({
    queryKey: [...QUERY_KEY, page, size],
    queryFn: async (): Promise<PaginatedResponse<PaymentListItem>> => {
      // Убираем fallback на моки - всегда используем реальный API
      return await paymentsApi.list(page, size)
    },
  })
}


