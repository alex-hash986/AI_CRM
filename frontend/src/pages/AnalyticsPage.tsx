import { useCallback, useState, type FormEvent } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getDashboard } from '../api/analytics'
import { Kpis } from '../components/Kpis'
import { LoadError, Loading } from '../components/ui'
import { money } from '../lib/format'
import { useLoad } from '../lib/useLoad'

export function AnalyticsPage() {
  const [currency, setCurrency] = useState('')
  const load = useCallback((signal: AbortSignal) => getDashboard(currency || undefined, signal), [currency])
  const { data, loading, error, reload } = useLoad(load)

  function chooseCurrency(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCurrency(String(new FormData(event.currentTarget).get('currency')).trim().toUpperCase())
  }

  return <div className="page">
    <div className="page-heading">
      <div><h1>Аналитика и прогнозы</h1><p>Выручка, конверсия и взвешенный прогноз по стадиям.</p></div>
      <form className="currency-control" onSubmit={chooseCurrency}>
        <input name="currency" aria-label="Валюта отчёта" placeholder={data?.currency ?? 'Валюта'} pattern="[A-Za-z]{3}" maxLength={3} />
        <button className="button button-secondary" type="submit">Применить</button>
      </form>
    </div>
    {loading && <Loading />}
    {error && <LoadError message={error} retry={reload} />}
    {data && !loading && <>
      <Kpis dashboard={data} />
      <section className="surface chart-panel">
        <h2>Выручка по стадиям</h2>
        <p>Бюджет всех сделок и взвешенный прогноз по активным.</p>
        {data.stages_breakdown.length === 0 ? <div className="empty-state">Нет стадий для отчёта.</div> :
          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.stages_breakdown.map(stage => ({
                ...stage, total: Number(stage.total_amount), weighted: Number(stage.weighted_amount),
              }))} margin={{ top: 16, right: 14, left: 8, bottom: 24 }} barGap={5}>
                <CartesianGrid stroke="#eaebf2" vertical={false} />
                <XAxis dataKey="stage_name" fontSize={11} tickLine={false} axisLine={false} height={46} interval={0} />
                <YAxis fontSize={11} tickLine={false} axisLine={false} width={72} tickFormatter={value =>
                  new Intl.NumberFormat('ru-RU', { notation: 'compact' }).format(value)} />
                <Tooltip formatter={value => money(Number(value), data.currency)} />
                <Legend />
                <Bar name="Сумма сделок" dataKey="total" fill="#7357dd" radius={[5, 5, 0, 0]} maxBarSize={42} />
                <Bar name="Взвешенный прогноз" dataKey="weighted" fill="#b9abf1" radius={[5, 5, 0, 0]} maxBarSize={42} />
              </BarChart>
            </ResponsiveContainer>
          </div>}
      </section>
    </>}
  </div>
}
