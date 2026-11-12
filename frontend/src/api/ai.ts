import type { DealScoringOutput, EmailDraft, EmailGenerateRequest, TaskStatus } from '../types'
import { api } from './apiClient'

export async function waitForTask<T extends object>(taskId: string, signal: AbortSignal): Promise<T> {
  const deadline = Date.now() + 90_000
  while (Date.now() < deadline) {
    const { data } = await api.get<TaskStatus<T>>(`/tasks/${taskId}`, { signal })
    if (data.status === 'SUCCESS' && data.result && !('error' in data.result)) return data.result
    if (['FAILURE', 'REVOKED', 'SUCCESS'].includes(data.status)) {
      throw new Error('AI-задача не вернула результат. Попробуйте ещё раз.')
    }
    await new Promise(resolve => window.setTimeout(resolve, 1000))
    signal.throwIfAborted()
  }
  throw new Error('AI-задача выполняется дольше обычного. Обновите карточку позже.')
}

export async function scoreDeal(id: number, signal: AbortSignal): Promise<DealScoringOutput> {
  const { data } = await api.post<TaskStatus<DealScoringOutput>>(`/deals/${id}/score`, null, { signal })
  return waitForTask(data.task_id, signal)
}

export async function generateEmail(data: EmailGenerateRequest, signal: AbortSignal): Promise<EmailDraft> {
  const { data: task } = await api.post<TaskStatus<EmailDraft>>('/emails/generate', data, { signal })
  return waitForTask(task.task_id, signal)
}
