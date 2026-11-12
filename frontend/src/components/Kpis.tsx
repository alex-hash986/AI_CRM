import { BadgeCheck, ChartNoAxesCombined, CircleDollarSign, Sparkles, Target } from 'lucide-react'
import { money, percent } from '../lib/format'
import type { SalesDashboard } from '../types'

export function Kpis({ dashboard, compact = false }: { dashboard: SalesDashboard; compact?: boolean }) {
  const currency = dashboard.currency
  const cards = [
    { label: 'Активная воронка', value: money(dashboard.total_pipeline_value, currency), icon: CircleDollarSign, color: 'violet' },
    { label: 'Взвешенный прогноз', value: money(dashboard.weighted_forecast_value, currency), icon: ChartNoAxesCombined, color: 'blue' },
    { label: 'Выиграно', value: money(dashboard.won_deals_revenue, currency), icon: BadgeCheck, color: 'green' },
    { label: 'Конверсия в победу', value: percent(dashboard.conversion_rate), icon: Target, color: 'amber' },
    { label: 'Средний AI-скоринг', value: dashboard.average_ai_score == null ? '—' : `${Math.round(dashboard.average_ai_score)} / 100`, icon: Sparkles, color: 'violet' },
  ]
  return <div className={`kpi-grid ${compact ? 'compact' : ''}`}>
    {cards.slice(0, compact ? 4 : 5).map(({ label, value, icon: Icon, color }) => <section className="kpi" key={label}>
      <div className={`metric-icon ${color}`}><Icon size={17} /></div>
      <div className="kpi-copy"><span>{label}</span><strong>{value}</strong></div>
    </section>)}
  </div>
}
