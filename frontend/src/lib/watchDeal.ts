import { getDeal } from '../api/deals'
import type { Deal } from '../types'

export async function watchDeal(
  id: number, ready: (deal: Deal) => boolean, signal: AbortSignal,
): Promise<Deal | null> {
  const deadline = Date.now() + 90_000
  while (Date.now() < deadline) {
    const deal = await getDeal(id, signal)
    if (ready(deal)) return deal
    await new Promise(resolve => window.setTimeout(resolve, 1600))
    signal.throwIfAborted()
  }
  return null
}
