import { useQuery } from '@tanstack/react-query'

import type { PaginatedResponse, PaymentListItem } from '@/lib/api'
import { paymentsApi } from '@/lib/api'
import { PAYMENTS_MOCK } from '@/lib/mocks/payments'

import { fetchWithFallback } from './utils'

const QUERY_KEY = ['payments', 'list']

export const usePayments = (page = 1, size = 50) => {
  return useQuery({
    queryKey: [...QUERY_KEY, page, size],
    queryFn: async (): Promise<PaginatedResponse<PaymentListItem>> =>
      fetchWithFallback(
        () => paymentsApi.list(page, size),
        () => ({
          items: PAYMENTS_MOCK.slice((page - 1) * size, page * size),
          total: PAYMENTS_MOCK.length,
          page,
          size,
        }),
        'payments list'
      ),
  })
}


