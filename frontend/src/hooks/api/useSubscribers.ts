import { useQuery } from '@tanstack/react-query'

import type { PaginatedResponse, SubscriberListItem } from '@/lib/api'
import { subscribersApi } from '@/lib/api'

export const SUBSCRIBERS_QUERY_KEY = ['subscribers', 'list'] as const

export const useSubscribers = (page = 1, size = 50) => {
  return useQuery({
    queryKey: [...SUBSCRIBERS_QUERY_KEY, page, size],
    queryFn: async (): Promise<PaginatedResponse<SubscriberListItem>> => {
      // Убираем fallback на моки - всегда используем реальный API
      return await subscribersApi.list(page, size)
    },
  })
}


