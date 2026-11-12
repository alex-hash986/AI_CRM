import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowUpRight, CheckCircle2, Send } from 'lucide-react'
import { waitForTask } from '../api/ai'
import { getDeal } from '../api/deals'
import { errorMessage } from '../api/apiClient'
import { simulateTelegram } from '../api/integrations'
import { ScoreBadge } from '../components/DealCard'
import { useToast } from '../components/Toast'
import { LoadError, Spinner } from '../components/ui'
import type { Deal, DealScoringOutput, TelegramResponse } from '../types'

export function IntegrationsPage({ onOpenDeal }: { onOpenDeal: (id: number) => void }) {
  const [pending, setPending] = useState(false)
  const [scoring, setScoring] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<TelegramResponse | null>(null)
  const [deal, setDeal] = useState<Deal | null>(null)
  const controller = useRef<AbortController | null>(null)
  const notify = useToast()
  useEffect(() => () => controller.current?.abort(), [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending) return
    controller.current?.abort()
    const request = new AbortController()
    controller.current = request
    const values = new FormData(event.currentTarget)
    const username = String(values.get('username')).trim().replace(/^@/, '')
    setError('')
    setResult(null)
    setDeal(null)
    setScoring(false)
    setPending(true)
    try {
      const response = await simulateTelegram({
        chat_id: String(values.get('chat_id')).trim(), username: username || undefined,
        text: String(values.get('text')).trim(),
      }, String(values.get('secret')))
      if (request.signal.aborted) return
      setResult(response)
      setPending(false)
      if (response.status === 'accepted' && response.deal_id !== null) {
        notify('Сообщение Telegram сохранено в CRM')
        if (response.task_id) {
          setScoring(true)
          await waitForTask<DealScoringOutput>(response.task_id, request.signal)
          const scored = await getDeal(response.deal_id, request.signal)
          if (!request.signal.aborted) {
            setDeal(scored)
            notify('AI-скоринг сделки готов')
          }
        } else {
          setError('Сообщение сохранено. Очередь AI-скоринга недоступна.')
        }
      }
    } catch (reason) {
      if (!request.signal.aborted) setError(errorMessage(reason))
    } finally {
      if (!request.signal.aborted) { setPending(false); setScoring(false) }
    }
  }

  return <div className="page">
    <div className="page-heading"><div><h1>Тест интеграций / Telegram</h1>
      <p>Проверьте, как входящее сообщение попадает в сделку и запускает AI-скоринг.</p></div></div>
    <div className="integration-grid">
      <section className="surface integration-card">
        <div className="integration-heading"><div className="metric-icon blue"><Send size={20} /></div><div><h2>Симулятор Telegram</h2><p>Входящее сообщение клиента</p></div></div>
        <form className="form-stack" onSubmit={submit}>
          <div className="form-row">
            <label>Chat ID<input name="chat_id" required inputMode="numeric" pattern="[0-9]{1,16}" placeholder="Например, 123456789" /></label>
            <label>Имя пользователя<input name="username" maxLength={255} placeholder="@username" /></label>
          </div>
          <label>Сообщение<textarea name="text" required rows={5} placeholder="Напишите, что клиент хочет узнать о продукте…" /></label>
          <label>Секрет webhook <small>Если настроен</small><input name="secret" type="password" autoComplete="off" /></label>
          <button className="button button-primary self-start" disabled={pending} type="submit">{pending ? <Spinner /> : <Send size={16} />} Отправить тестовое сообщение</button>
        </form>
      </section>
      <section className="surface integration-card result-card">
        <h2>Результат</h2>
        {error && <LoadError message={error} />}
        {!result && !error && <p className="body-copy">Здесь появится результат обработки сообщения.</p>}
        {result?.status === 'accepted' && <div className="notice success"><CheckCircle2 size={17} /> Сообщение сохранено в CRM</div>}
        {result?.status === 'duplicate' && <p className="body-copy">Это сообщение уже обработано.</p>}
        {result?.status === 'ignored' && <p className="body-copy">Webhook пропустил сообщение.</p>}
        {scoring && <div className="inline-loading" role="status"><Spinner /> Ожидаем AI-скоринг…</div>}
        {deal && <div className="integration-deal"><strong>{deal.title}</strong><ScoreBadge score={deal.ai_score} /></div>}
        {result?.deal_id != null && <button className="button button-secondary self-start" onClick={() => onOpenDeal(result.deal_id!)}>
          Открыть сделку <ArrowUpRight size={15} />
        </button>}
      </section>
    </div>
  </div>
}
