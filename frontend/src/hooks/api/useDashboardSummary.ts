import { useQuery } from '@tanstack/react-query'

import { DASHBOARD_SUMMARY_MOCK, type DashboardSummary } from '@/lib/mocks/dashboard'

import { fetchWithFallback, get } from './utils'

const QUERY_KEY = ['dashboard', 'summary']

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async (): Promise<DashboardSummary> =>
      fetchWithFallback(
        () => get<DashboardSummary>({ url: '/dashboard/summary' }),
        () => DASHBOARD_SUMMARY_MOCK,
        'dashboard summary'
      ),
  })
}


