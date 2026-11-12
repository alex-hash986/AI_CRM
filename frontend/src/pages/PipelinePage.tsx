import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { DropResult } from '@hello-pangea/dnd'
import { LayoutGrid, Plus, Search } from 'lucide-react'
import { getDashboard } from '../api/analytics'
import { errorMessage } from '../api/apiClient'
import { getClients } from '../api/clients'
import { moveDeal } from '../api/deals'
import { getBoard } from '../api/pipelines'
import { CreateDealModal } from '../components/CreateDealModal'
import { KanbanBoard } from '../components/KanbanBoard'
import { Kpis } from '../components/Kpis'
import { useToast } from '../components/Toast'
import { LoadError, Loading } from '../components/ui'
import { useLoad } from '../lib/useLoad'
import { watchDeal } from '../lib/watchDeal'
import type { BoardStage, Deal } from '../types'

async function loadPipeline(signal: AbortSignal) {
  const [board, clients] = await Promise.all([getBoard(signal), getClients(signal)])
  return { board, clients }
}

export function PipelinePage({ onOpenDeal, changedDeal }: {
  onOpenDeal: (id: number) => void; changedDeal: Deal | null
}) {
  const notify = useToast()
  const pipeline = useLoad(loadPipeline)
  const [stages, setStages] = useState<BoardStage[]>([])
  const [search, setSearch] = useState('')
  const [currency, setCurrency] = useState('')
  const [createIn, setCreateIn] = useState<number | null>(null)
  const [moving, setMoving] = useState(false)
  const activeMove = useRef(false)
  const tracking = useRef(new Map<number, AbortController>())
  const clients = useMemo(() => new Map((pipeline.data?.clients ?? []).map(client => [client.id, client])), [pipeline.data])
  const currencies = [...new Set(stages.flatMap(stage => stage.deals.map(deal => deal.currency)))].sort()
  const selectedCurrency = currencies.includes(currency) ? currency : currencies[0]
  const loadKpis = useCallback((signal: AbortSignal) => getDashboard(selectedCurrency, signal), [selectedCurrency])
  const metrics = useLoad(loadKpis)
  const query = search.trim().toLocaleLowerCase('ru-RU')
  const filtered = stages.map(stage => ({
    ...stage, deals: stage.deals.filter(deal => {
      const client = clients.get(deal.client_id)
      return [deal.title, client?.name, client?.company].some(value => value?.toLocaleLowerCase('ru-RU').includes(query))
    }),
  }))
  const totalDeals = stages.reduce((total, stage) => total + stage.deals.length, 0)

  useEffect(() => {
    if (pipeline.data) setStages(pipeline.data.board.stages)
  }, [pipeline.data])

  const replaceDeal = useCallback((deal: Deal) => {
    setStages(previous => previous.map(stage => stage.id !== deal.stage_id ? stage : {
      ...stage, deals: stage.deals.map(item => item.id === deal.id ? deal : item),
    }))
  }, [])

  useEffect(() => {
    if (changedDeal) replaceDeal(changedDeal)
  }, [changedDeal, replaceDeal])

  useEffect(() => {
    const controllers = tracking.current
    return () => controllers.forEach(controller => controller.abort())
  }, [])

  function onDrop({ source, destination, draggableId }: DropResult) {
    if (!destination || source.droppableId === destination.droppableId || activeMove.current) return
    const sourceId = Number(source.droppableId)
    const targetId = Number(destination.droppableId)
    const dealId = Number(draggableId)
    const original = stages.find(stage => stage.id === sourceId)?.deals.find(deal => deal.id === dealId)
    const target = stages.find(stage => stage.id === targetId)
    if (!original || !target) return
    activeMove.current = true
    setMoving(true)
    tracking.current.get(dealId)?.abort()
    const nextVisible = filtered.find(stage => stage.id === targetId)?.deals[destination.index]
    const insertion = nextVisible ? target.deals.findIndex(deal => deal.id === nextVisible.id) : target.deals.length
    setStages(previous => previous.map(stage => {
      if (stage.id === sourceId) return { ...stage, deals: stage.deals.filter(deal => deal.id !== dealId) }
      if (stage.id !== targetId) return stage
      return { ...stage, deals: [
        ...stage.deals.slice(0, insertion), { ...original, stage_id: targetId }, ...stage.deals.slice(insertion),
      ] }
    }))

    void moveDeal(dealId, targetId).then(updated => {
      replaceDeal(updated)
      metrics.reload()
      notify(`Сделка перемещена · ${target.name}`)
      if (target.is_won || target.is_lost) return
      const controller = new AbortController()
      tracking.current.set(dealId, controller)
      void watchDeal(dealId, deal => deal.stage_id !== targetId || deal.updated_at !== updated.updated_at, controller.signal)
        .then(deal => {
          if (deal?.stage_id === targetId && !controller.signal.aborted) {
            replaceDeal(deal)
            metrics.reload()
          }
        })
        .catch(() => { /* The stage change has already been saved. */ })
        .finally(() => {
          if (tracking.current.get(dealId) === controller) tracking.current.delete(dealId)
        })
    }, reason => {
      const originalIndex = stages.find(stage => stage.id === sourceId)?.deals.findIndex(deal => deal.id === dealId) ?? 0
      setStages(previous => previous.map(stage => {
        if (stage.id === targetId) return { ...stage, deals: stage.deals.filter(deal => deal.id !== dealId) }
        if (stage.id !== sourceId) return stage
        return { ...stage, deals: [...stage.deals.slice(0, originalIndex), original, ...stage.deals.slice(originalIndex)] }
      }))
      notify(errorMessage(reason), 'error')
    }).finally(() => {
      activeMove.current = false
      setMoving(false)
    })
  }

  function onCreated(deal: Deal) {
    setStages(previous => previous.map(stage => stage.id === deal.stage_id ? { ...stage, deals: [...stage.deals, deal] } : stage))
    setCreateIn(null)
    metrics.reload()
    notify('Сделка создана')
  }

  return <div className="page pipeline-page">
    <div className="page-heading">
      <div><h1>Воронка продаж</h1><p>Управляйте сделками и отслеживайте прогноз выручки.</p></div>
      <button className="button button-primary" disabled={stages.length === 0} onClick={() => setCreateIn(stages[0].id)}>
        <Plus size={17} /> Новая сделка
      </button>
    </div>
    {metrics.data ? <Kpis dashboard={metrics.data} compact /> : metrics.loading ? <Loading label="Считаем показатели…" />
      : <LoadError message={metrics.error} retry={metrics.reload} />}
    <section className="board-panel" aria-label="Доска сделок">
      <div className="board-toolbar">
        <div className="board-label"><LayoutGrid size={17} /><h2>Доска сделок</h2><span className="total-count">{totalDeals}</span></div>
        <div className="toolbar-actions">
          {currencies.length > 1 && <select aria-label="Валюта сводки" value={selectedCurrency}
            onChange={event => setCurrency(event.target.value)}>{currencies.map(code => <option key={code}>{code}</option>)}</select>}
          <label className="search-control"><Search size={16} /><input aria-label="Поиск сделок" placeholder="Поиск сделок…"
            value={search} onChange={event => setSearch(event.target.value)} /></label>
        </div>
      </div>
      {pipeline.error ? <LoadError message={pipeline.error} retry={pipeline.reload} /> : pipeline.loading ? <Loading />
        : stages.length === 0 ? <div className="empty-state">В воронке пока нет стадий.</div>
          : <KanbanBoard stages={filtered} clients={clients} onOpen={onOpenDeal} onAdd={setCreateIn} onDrop={onDrop} moving={moving} />}
    </section>
    {createIn !== null && <CreateDealModal stages={stages} clients={pipeline.data?.clients ?? []}
      initialStage={createIn} onClose={() => setCreateIn(null)} onCreated={onCreated} />}
  </div>
}
