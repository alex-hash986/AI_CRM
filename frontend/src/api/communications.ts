import type { Communication, CommunicationCreate, CommunicationCreated, EmailSendRequest, EmailSendResponse } from '../types'
import { api } from './apiClient'

export async function getDealCommunications(id: number, signal?: AbortSignal): Promise<Communication[]> {
  return (await api.get<Communication[]>(`/deals/${id}/communications`, { signal })).data
}

export async function createCommunication(data: CommunicationCreate): Promise<CommunicationCreated> {
  return (await api.post<CommunicationCreated>('/communications', data)).data
}

export async function sendEmail(data: EmailSendRequest): Promise<EmailSendResponse> {
  return (await api.post<EmailSendResponse>('/integrations/email/send', data)).data
}
