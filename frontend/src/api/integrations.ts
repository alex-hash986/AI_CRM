import type { TelegramRequest, TelegramResponse } from '../types'
import { api } from './apiClient'

export async function simulateTelegram(data: TelegramRequest, secret: string): Promise<TelegramResponse> {
  return (await api.post<TelegramResponse>('/integrations/telegram/webhook', data, {
    headers: secret ? { 'X-Telegram-Bot-Api-Secret-Token': secret } : undefined,
  })).data
}
