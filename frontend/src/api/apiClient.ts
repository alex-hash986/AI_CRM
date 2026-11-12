import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 20_000,
})

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError<{ detail?: string | { msg: string }[] }>(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      const translations: Record<string, string> = {
        'Pipeline not found': 'Воронка не найдена.',
        'Deal not found': 'Сделка не найдена.',
        'Client not found': 'Клиент не найден.',
        'Task queue unavailable': 'Очередь AI-задач недоступна.',
        'Task result backend unavailable': 'Хранилище результатов AI-задач недоступно.',
        'Invalid Telegram webhook secret': 'Неверный секрет Telegram webhook.',
        'Telegram webhook secret is not configured': 'Секрет Telegram webhook не настроен на сервере.',
        'Specify currency for a multi-currency dashboard': 'Выберите валюту для отчёта.',
        'SMTP delivery failed': 'SMTP-сервер не принял письмо.',
      }
      return translations[detail] ?? detail
    }
    if (Array.isArray(detail)) return detail.map(item => item.msg).join('. ')
    if (!error.response) return 'Нет связи с сервером. Попробуйте ещё раз.'
    return `Запрос завершился ошибкой (${error.response.status}).`
  }
  return error instanceof Error ? error.message : 'Не удалось выполнить действие.'
}
