import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  plansApi,
  type SubscriptionPlan,
  type SubscriptionPlanCreatePayload,
  type SubscriptionPlanUpdatePayload,
} from '@/lib/api'

import { getAxiosErrorMessage } from './utils'

export const PLANS_QUERY_KEY = ['plans'] as const

export const usePlans = () => {
  return useQuery<SubscriptionPlan[]>({
    queryKey: PLANS_QUERY_KEY,
    queryFn: () => plansApi.list(),
  })
}

export const useCreatePlanMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SubscriptionPlanCreatePayload) => plansApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PLANS_QUERY_KEY })
    },
  })
}

export const useUpdatePlanMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      planId,
      payload,
    }: {
      planId: number
      payload: SubscriptionPlanUpdatePayload
    }) => plansApi.update(planId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PLANS_QUERY_KEY })
    },
  })
}

export const useDeletePlanMutation = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (planId: number) => plansApi.remove(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PLANS_QUERY_KEY })
    },
  })
}

export { getAxiosErrorMessage }


