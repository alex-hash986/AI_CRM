import { useCallback, useState } from 'react'
import { ArrowUpRight, Search, UsersRound } from 'lucide-react'
import { getClient, getClients } from '../api/clients'
import { Dialog, LoadError, Loading } from '../components/ui'
import { ScoreBadge } from '../components/DealCard'
import { initials, money } from '../lib/format'
import { useLoad } from '../lib/useLoad'

function ClientDeals({ id, onClose, onOpenDeal }: { id: number; onClose: () => void; onOpenDeal: (id: number) => void }) {
  const load = useCallback((signal: AbortSignal) => getClient(id, signal), [id])
  const { data, error, loading, reload } = useLoad(load)
  return <Dialog title={data?.company || data?.name || 'Карточка клиента'} onClose={onClose} drawer>
    <div className="dialog-body form-stack">
      {loading && <Loading />}
      {error && <LoadError message={error} retry={reload} />}
      {data && <>
        <div className="client-contact">
          <strong>{data.name}</strong>
          {data.email && <a href={`mailto:${data.email}`}>{data.email}</a>}
          {data.phone && <a href={`tel:${data.phone}`}>{data.phone}</a>}
        </div>
        <h3>Сделки клиента</h3>
        {data.deals.length === 0 ? <p className="body-copy">Сделок пока нет.</p> : <ul className="client-deals">
          {data.deals.map(deal => <li key={deal.id}><button onClick={() => { onClose(); onOpenDeal(deal.id) }}>
            <div><strong>{deal.title}</strong><span>{money(deal.budget, deal.currency)}</span></div>
            <ScoreBadge score={deal.ai_score} /><ArrowUpRight size={16} />
          </button></li>)}
        </ul>}
      </>}
    </div>
  </Dialog>
}

export function ClientsPage({ onOpenDeal }: { onOpenDeal: (id: number) => void }) {
  const { data, loading, error, reload } = useLoad(getClients)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<number | null>(null)
  const query = search.trim().toLocaleLowerCase('ru-RU')
  const rows = data?.filter(client => [client.name, client.company, client.email, client.phone].some(value =>
    value?.toLocaleLowerCase('ru-RU').includes(query))) ?? []

  return <div className="page">
    <div className="page-heading"><div><h1>Клиенты</h1><p>Контакты, компании и связанные сделки.</p></div></div>
    <section className="surface clients-panel">
      <div className="board-toolbar">
        <div className="board-label"><UsersRound size={17} /><h2>Все клиенты</h2><span className="total-count">{data?.length ?? 0}</span></div>
        <label className="search-control"><Search size={16} /><input aria-label="Поиск клиентов" placeholder="Имя, компания или email…"
          value={search} onChange={event => setSearch(event.target.value)} /></label>
      </div>
      {loading ? <Loading /> : error ? <LoadError message={error} retry={reload} /> : rows.length === 0 ?
        <div className="empty-state">{query ? 'Клиенты по запросу не найдены.' : 'В CRM пока нет клиентов.'}</div> :
        <div className="table-scroll"><table>
          <thead><tr><th>Клиент</th><th>Компания</th><th>Email</th><th>Телефон</th><th>Статус</th><th><span className="sr-only">Действие</span></th></tr></thead>
          <tbody>{rows.map(client => <tr key={client.id}>
            <td><button className="client-link" onClick={() => setSelected(client.id)}><span className="client-avatar" aria-hidden="true">{initials(client.name)}</span>{client.name}</button></td>
            <td>{client.company ?? '—'}</td><td>{client.email ?? '—'}</td><td>{client.phone ?? '—'}</td>
            <td><span className={`client-status ${client.status === 'active' ? 'active' : ''}`}>{client.status === 'active' ? 'Активный' : client.status}</span></td>
            <td><button className="icon-button" aria-label={`Открыть сделки клиента ${client.name}`} onClick={() => setSelected(client.id)}><ArrowUpRight size={17} /></button></td>
          </tr>)}</tbody>
        </table></div>}
    </section>
    {selected !== null && <ClientDeals key={selected} id={selected} onClose={() => setSelected(null)} onOpenDeal={onOpenDeal} />}
  </div>
}
