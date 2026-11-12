import type { Deal, DealCreate } from '../types'
import { api } from './apiClient'

export async function getDeal(id: number, signal?: AbortSignal): Promise<Deal> {
  return (await api.get<Deal>(`/deals/${id}`, { signal })).data
}

export async function createDeal(data: DealCreate): Promise<Deal> {
  return (await api.post<Deal>('/deals/', data)).data
}

export async function moveDeal(id: number, stageId: number): Promise<Deal> {
  return (await api.patch<Deal>(`/deals/${id}/stage`, { stage_id: stageId })).data
}
