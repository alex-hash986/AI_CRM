import { useState, type FormEvent } from 'react'
import { errorMessage } from '../api/apiClient'
import { createDeal } from '../api/deals'
import type { Client, Deal, PipelineStage } from '../types'
import { Dialog, LoadError, Spinner } from './ui'

export function CreateDealModal({ stages, clients, initialStage, onClose, onCreated }: {
  stages: PipelineStage[]; clients: Client[]; initialStage: number
  onClose: () => void; onCreated: (deal: Deal) => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    const data = new FormData(event.currentTarget)
    setError('')
    setBusy(true)
    try {
      const deal = await createDeal({
        title: String(data.get('title')).trim(),
        budget: String(data.get('budget')),
        currency: String(data.get('currency')).trim().toUpperCase(),
        client_id: Number(data.get('client')),
        stage_id: Number(data.get('stage')),
      })
      onCreated(deal)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setBusy(false)
    }
  }

  return <Dialog title="Новая сделка" onClose={onClose}>
    <form className="dialog-body form-stack" onSubmit={submit}>
      <label>Название сделки<input autoFocus name="title" required maxLength={255} placeholder="Например, внедрение CRM" /></label>
      <label>Клиент<select name="client" aria-label="Клиент" required defaultValue="">
        <option value="" disabled>Выберите клиента</option>
        {clients.map(client => <option key={client.id} value={client.id}>
          {client.company ? `${client.company} · ${client.name}` : client.name}
        </option>)}
      </select></label>
      <div className="form-row">
        <label>Бюджет<input name="budget" inputMode="decimal" type="number" required min="0" step="0.01" placeholder="0" /></label>
        <label>Валюта<input name="currency" pattern="[A-Za-z]{3}" maxLength={3} required defaultValue="RUB" /></label>
      </div>
      <label>Стадия<select name="stage" aria-label="Стадия" defaultValue={initialStage} required>
        {stages.map(stage => <option key={stage.id} value={stage.id}>{stage.name}</option>)}
      </select></label>
      {error && <LoadError message={error} />}
      <div className="form-actions">
        <button className="button button-secondary" type="button" onClick={onClose}>Отмена</button>
        <button className="button button-primary" type="submit" disabled={busy || clients.length === 0}>
          {busy && <Spinner />} Создать сделку
        </button>
      </div>
    </form>
  </Dialog>
}
