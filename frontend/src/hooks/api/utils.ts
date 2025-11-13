import { apiClient } from '@/lib/api'
import type { AxiosRequestConfig } from 'axios'
import { isAxiosError } from 'axios'

type RequestConfig<T> = AxiosRequestConfig<T> & {
  url: string
  method?: 'get' | 'post' | 'put' | 'patch' | 'delete'
}

export async function fetchWithFallback<TResponse>(
  request: () => Promise<TResponse>,
  fallback: () => TResponse,
  context: string
): Promise<TResponse> {
  try {
    return await request()
  } catch (error) {
    console.warn(`API request failed for ${context}. Using fallback data.`, error)
    return fallback()
  }
}

export const get = async <TResponse>(
  config: RequestConfig<unknown>
): Promise<TResponse> => {
  const response = await apiClient.request<TResponse>({
    method: 'get',
    ...config,
  })
  return response.data
}

export const getAxiosErrorMessage = (error: unknown, fallback: string) => {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
  }
  return fallback
}


