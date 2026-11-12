import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowUpRight, Mail, MessageSquareText, Phone, Send, Sparkles, WandSparkles } from 'lucide-react'
import { generateEmail, scoreDeal, waitForTask } from '../api/ai'
import { errorMessage } from '../api/apiClient'
import { getClient } from '../api/clients'
import { createCommunication, getDealCommunications, sendEmail } from '../api/communications'
import { getDeal } from '../api/deals'
import { dateTime, money, percent } from '../lib/format'
import { useLoad } from '../lib/useLoad'
import type { Channel, Communication, Deal, DealScoringOutput, EmailDraft, EmailTemplate, EmailTone } from '../types'
import { ScoreBadge } from './DealCard'
import { useToast } from './Toast'
import { Dialog, LoadError, Loading, Spinner } from './ui'

const channels = {
  email: { label: 'Email', icon: Mail },
  telegram: { label: 'Telegram', icon: Send },
  call: { label: 'Звонок', icon: Phone },
  note: { label: 'Заметка', icon: MessageSquareText },
} satisfies Record<Channel, { label: string; icon: typeof Mail }>

const templates: Record<EmailTemplate, string> = {
  follow_up: 'Продолжение общения',
  cold_outreach: 'Первый контакт',
  proposal_pitch: 'Коммерческое предложение',
  reengagement: 'Возобновление общения',
}

export function DealDrawer({ id, onClose, onDealChange }: {
  id: number; onClose: () => void; onDealChange: (deal: Deal) => void
}) {
  const notify = useToast()
  const load = useCallback(async (signal: AbortSignal) => {
    const [deal, logs] = await Promise.all([getDeal(id, signal), getDealCommunications(id, signal)])
    const client = await getClient(deal.client_id, signal)
    return { deal, logs, client }
  }, [id])
  const { data, loading, error, reload } = useLoad(load)
  const [tab, setTab] = useState<'ai' | 'history'>('ai')
  const [currentDeal, setCurrentDeal] = useState<Deal | null>(null)
  const [addedLogs, setAddedLogs] = useState<Communication[]>([])
  const [draft, setDraft] = useState<EmailDraft | null>(null)
  const [template, setTemplate] = useState<EmailTemplate>('follow_up')
  const [tone, setTone] = useState<EmailTone>('friendly')
  const [recipient, setRecipient] = useState<string | null>(null)
  const [busy, setBusy] = useState<'score' | 'generate' | 'send' | 'note' | null>(null)
  const [feedback, setFeedback] = useState('')
  const [actionError, setActionError] = useState('')
  const [trackingNote, setTrackingNote] = useState(false)
  const request = useRef<AbortController | null>(null)
  const noteTracking = useRef<AbortController | null>(null)
  const deal = currentDeal ?? data?.deal
  const logs = [...addedLogs, ...(data?.logs ?? [])].filter((log, index, entries) =>
    entries.findIndex(entry => entry.id === log.id) === index,
  )

  useEffect(() => () => {
    request.current?.abort()
    noteTracking.current?.abort()
  }, [])

  function applyDeal(updated: Deal) {
    setCurrentDeal(previous => previous && previous.updated_at > updated.updated_at ? previous : updated)
    onDealChange(updated)
  }

  async function perform(action: NonNullable<typeof busy>, work: (signal: AbortSignal) => Promise<void>) {
    if (busy) return
    setBusy(action)
    setFeedback('')
    setActionError('')
    const controller = new AbortController()
    request.current = controller
    try {
      await work(controller.signal)
    } catch (reason) {
      if (!controller.signal.aborted) {
        setActionError(errorMessage(reason))
        notify(errorMessage(reason), 'error')
      }
    } finally {
      if (!controller.signal.aborted) setBusy(null)
    }
  }

  function showSuccess(message: string) {
    setFeedback(message)
    notify(message)
  }

  function addNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!deal) return
    const form = event.currentTarget
    const values = new FormData(form)
    const channel = values.get('channel') === 'call' ? 'call' : 'note'
    void perform('note', async signal => {
      const log = await createCommunication({
        deal_id: deal.id, client_id: deal.client_id, channel,
        direction: 'outbound', content: String(values.get('content')).trim(),
      })
      if (signal.aborted) return
      setAddedLogs(previous => [log, ...previous])
      form.reset()
      showSuccess(channel === 'note' ? 'Заметка добавлена' : 'Звонок записан')
      noteTracking.current?.abort()
      if (!log.task_id) {
        setTrackingNote(false)
        applyDeal(await getDeal(deal.id, signal))
        return
      }

      const controller = new AbortController()
      noteTracking.current = controller
      setTrackingNote(true)
      void waitForTask<DealScoringOutput>(log.task_id, controller.signal).then(() => getDeal(deal.id, controller.signal))
        .then(updated => {
          if (updated && !controller.signal.aborted) {
            applyDeal(updated)
            showSuccess('AI-анализ обновлён по заметке')
          }
        })
        .catch(reason => { if (!controller.signal.aborted) setActionError(errorMessage(reason)) })
        .finally(() => { if (!controller.signal.aborted) setTrackingNote(false) })
    })
  }

  return <Dialog title={deal?.title ?? 'Сделка'} onClose={onClose} drawer>
    {loading && <Loading label="Загружаем сделку…" />}
    {error && <LoadError message={error} retry={reload} />}
    {deal && data && <>
      <div className="drawer-meta">
        <span>{data.client.company || data.client.name}</span>
        <strong>{money(deal.budget, deal.currency)}</strong>
      </div>
      <div className="drawer-tabs" role="tablist" aria-label="Разделы сделки">
        <button type="button" role="tab" aria-selected={tab === 'ai'} onClick={() => setTab('ai')}><Sparkles size={16} /> AI-Ассистент</button>
        <button type="button" role="tab" aria-selected={tab === 'history'} onClick={() => setTab('history')}><MessageSquareText size={16} /> История и заметки</button>
      </div>
      <div className="dialog-body drawer-content" role="tabpanel" aria-label={tab === 'ai' ? 'AI-Ассистент' : 'История и заметки'}>
        {actionError && <LoadError message={actionError} />}
        {feedback && <p className="notice success" role="status">{feedback}</p>}
        {tab === 'ai' ? <>
          <section className="drawer-section">
            <div className="section-line"><h3>AI-скоринг и риски</h3><ScoreBadge score={deal.ai_score} /></div>
            <div className="progress-track" role="progressbar" aria-label="AI-скоринг" aria-valuemin={0} aria-valuemax={100}
              aria-valuenow={deal.ai_score ?? undefined}><span style={{ width: `${deal.ai_score ?? 0}%` }} /></div>
            <div className="probability-line">Вероятность закрытия <strong>{deal.ai_win_probability == null ? '—' : percent(deal.ai_win_probability * 100)}</strong></div>
            <h4>Оценка рисков</h4><p className="body-copy">{deal.ai_risk_assessment ?? 'Для этой сделки ещё нет оценки рисков.'}</p>
            {deal.ai_next_step && <div className="recommendation"><ArrowUpRight size={18} /><div><h4>Рекомендуемый следующий шаг</h4><p>{deal.ai_next_step}</p></div></div>}
            <button className="button button-secondary" disabled={!!busy} onClick={() => void perform('score', async signal => {
              await scoreDeal(id, signal)
              applyDeal(await getDeal(id, signal))
              showSuccess('AI-анализ обновлён')
            })}>{busy === 'score' ? <Spinner /> : <Sparkles size={15} />} Пересчитать AI-анализ</button>
          </section>
          <section className="drawer-section form-stack">
            <h3>AI-генератор писем</h3>
            <div className="form-row">
              <label>Шаблон<select value={template} onChange={event => setTemplate(event.target.value as EmailTemplate)}>
                {Object.entries(templates).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select></label>
              <label>Тон<select value={tone} onChange={event => setTone(event.target.value as EmailTone)}>
                <option value="friendly">Дружелюбный</option><option value="formal">Формальный</option><option value="direct">Прямой</option>
              </select></label>
            </div>
            <button className="button button-primary self-start" disabled={!!busy} onClick={() => void perform('generate', async signal => {
              setDraft(await generateEmail({ deal_id: id, template_type: template, tone }, signal))
              showSuccess('Черновик готов')
            })}>{busy === 'generate' ? <Spinner /> : <WandSparkles size={16} />} Сгенерировать</button>
            {draft && <form className="form-stack draft" onSubmit={event => {
              event.preventDefault()
              void perform('send', async signal => {
                const result = await sendEmail({
                  deal_id: id, to_email: recipient ?? data.client.email ?? '', subject: draft.subject.trim(), body: draft.body.trim(),
                })
                if (signal.aborted) return
                setAddedLogs(previous => [result.communication, ...previous])
                showSuccess(result.delivery_mode === 'demo' ? 'Демо-отправка записана в историю' : 'Письмо отправлено клиенту')
              })
            }}>
              <label>Получатель<input type="email" required value={recipient ?? data.client.email ?? ''}
                onChange={event => setRecipient(event.target.value)} /></label>
              <label>Тема<input required maxLength={255} value={draft.subject}
                onChange={event => setDraft({ ...draft, subject: event.target.value })} /></label>
              <label>Текст письма<textarea required rows={8} value={draft.body}
                onChange={event => setDraft({ ...draft, body: event.target.value })} /></label>
              <button className="button button-primary self-start" disabled={!!busy} type="submit">
                {busy === 'send' ? <Spinner /> : <Send size={16} />} Отправить письмо клиенту
              </button>
            </form>}
          </section>
        </> : <>
          <form className="drawer-section form-stack" onSubmit={addNote}>
            <h3>Добавить коммуникацию</h3>
            <label>Тип записи<select name="channel"><option value="note">Заметка</option><option value="call">Звонок</option></select></label>
            <label>Текст<textarea name="content" required rows={3} placeholder="Что обсудили с клиентом?" /></label>
            <button className="button button-primary self-start" disabled={!!busy} type="submit">{busy === 'note' && <Spinner />} Сохранить запись</button>
            {trackingNote && <div className="inline-loading" role="status"><Spinner /> Обновляем AI-анализ…</div>}
          </form>
          <section className="drawer-section">
            <h3>История коммуникаций</h3>
            {logs.length === 0 ? <p className="body-copy mt-3">Пока нет записей.</p> : <ol className="timeline">
              {logs.map(log => {
                const { icon: Icon, label } = channels[log.channel]
                return <li key={log.id}><span className="timeline-icon"><Icon size={15} /></span>
                  <div><div className="timeline-head"><strong>{label}</strong><time dateTime={log.created_at}>{dateTime(log.created_at)}</time></div>
                  <p>{log.content}</p>{log.ai_summary && <small>{log.ai_summary}</small>}</div>
                </li>
              })}
            </ol>}
          </section>
        </>}
      </div>
    </>}
  </Dialog>
}
