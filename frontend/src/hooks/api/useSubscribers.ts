import { useQuery } from '@tanstack/react-query'

import type { PaginatedResponse, SubscriberListItem } from '@/lib/api'
import { subscribersApi } from '@/lib/api'
import { SUBSCRIBERS_MOCK } from '@/lib/mocks/subscribers'

import { fetchWithFallback } from './utils'

export const SUBSCRIBERS_QUERY_KEY = ['subscribers', 'list'] as const

export const useSubscribers = (page = 1, size = 50) => {
  return useQuery({
    queryKey: [...SUBSCRIBERS_QUERY_KEY, page, size],
    queryFn: async (): Promise<PaginatedResponse<SubscriberListItem>> =>
      fetchWithFallback(
        () => subscribersApi.list(page, size),
        () => ({
          items: SUBSCRIBERS_MOCK.slice((page - 1) * size, page * size),
          total: SUBSCRIBERS_MOCK.length,
          page,
          size,
        }),
        'subscribers list'
      ),
  })
}


