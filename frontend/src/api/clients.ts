import type { Client, ClientDetail, PaginatedResponse } from '../types'
import { api } from './apiClient'

export async function getClients(signal?: AbortSignal): Promise<Client[]> {
  const clients: Client[] = []
  const limit = 100
  let total: number
  do {
    const page = (await api.get<PaginatedResponse<Client>>('/clients/', {
      params: { limit, offset: clients.length }, signal,
    })).data
    if (page.items.length === 0) break
    clients.push(...page.items)
    total = page.total
  } while (clients.length < total)
  return clients
}

export async function getClient(id: number, signal?: AbortSignal): Promise<ClientDetail> {
  return (await api.get<ClientDetail>(`/clients/${id}`, { signal })).data
}
