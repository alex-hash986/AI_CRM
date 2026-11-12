import type { SalesDashboard } from '../types'
import { api } from './apiClient'

export async function getDashboard(currency?: string, signal?: AbortSignal): Promise<SalesDashboard> {
  return (await api.get<SalesDashboard>('/analytics/dashboard', { params: { currency }, signal })).data
}
