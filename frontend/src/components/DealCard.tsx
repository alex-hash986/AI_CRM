import { Building2, GripVertical, Sparkles } from 'lucide-react'
import type { DraggableProvided } from '@hello-pangea/dnd'
import { money, percent } from '../lib/format'
import type { DealShort } from '../types'

export function ScoreBadge({ score }: { score: number | null }) {
  const band = score == null ? 'neutral' : score >= 75 ? 'good' : score >= 40 ? 'medium' : 'low'
  return <span className={`score-pill ${band}`} title="AI-скоринг"><Sparkles size={12} />{score ?? '—'}</span>
}

export function DealCard({ deal, company, onOpen, provided, dragging }: {
  deal: DealShort; company: string; onOpen: (id: number) => void
  provided: DraggableProvided; dragging: boolean
}) {
  return <article ref={provided.innerRef} {...provided.draggableProps} className={`deal-card ${dragging ? 'dragging' : ''}`}>
    <div className="deal-card-header">
      <button type="button" className="deal-title" onClick={() => onOpen(deal.id)}>{deal.title}</button>
      <span className="drag-handle" {...provided.dragHandleProps} aria-label={`Переместить сделку «${deal.title}»`}>
        <GripVertical size={16} />
      </span>
    </div>
    <div className="deal-company"><Building2 size={13} /><span title={company}>{company}</span></div>
    <div className="deal-budget">{money(deal.budget, deal.currency)}</div>
    <footer className="deal-card-footer">
      <ScoreBadge score={deal.ai_score} />
      <span title="Вероятность закрытия">{deal.ai_win_probability == null ? '—' : percent(deal.ai_win_probability * 100)}</span>
    </footer>
  </article>
}
