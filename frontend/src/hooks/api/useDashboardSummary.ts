import { useQuery } from '@tanstack/react-query'

import type { DashboardSummary } from '@/lib/mocks/dashboard'

import { get } from './utils'

const QUERY_KEY = ['dashboard', 'summary']

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async (): Promise<DashboardSummary> => {
      // Убираем fallback на моки - всегда используем реальный API
      return await get<DashboardSummary>({ url: '/dashboard/summary' })
    },
  })
}


