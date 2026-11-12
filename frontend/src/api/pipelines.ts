import type { Board } from '../types'
import { api } from './apiClient'

export async function getBoard(signal?: AbortSignal): Promise<Board> {
  return (await api.get<Board>('/pipelines/board', { signal })).data
}
