import { lazy, Suspense, useEffect, useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { api } from './api/apiClient'
import { DealDrawer } from './components/DealDrawer'
import { navigation, Sidebar, type Page } from './components/Sidebar'
import { ToastProvider } from './components/Toast'
import { useLoad } from './lib/useLoad'
import { Loading } from './components/ui'
import { ClientsPage } from './pages/ClientsPage'
import { IntegrationsPage } from './pages/IntegrationsPage'
import { PipelinePage } from './pages/PipelinePage'
import type { Deal } from './types'

const AnalyticsPage = lazy(async () => ({ default: (await import('./pages/AnalyticsPage')).AnalyticsPage }))

function getPage(): Page {
  const hash = window.location.hash.slice(1)
  return navigation.find(page => page.id === hash)?.id ?? 'pipeline'
}

async function loadHealth(signal: AbortSignal) {
  return (await api.get<{ status: string }>('/health', { signal })).data.status
}

export default function App() {
  const [page, setPage] = useState(getPage)
  const [dealId, setDealId] = useState<number | null>(null)
  const [changedDeal, setChangedDeal] = useState<Deal | null>(null)
  const health = useLoad(loadHealth)

  useEffect(() => {
    function navigate() {
      setPage(getPage())
      setDealId(null)
      setChangedDeal(null)
    }
    window.addEventListener('hashchange', navigate)
    return () => window.removeEventListener('hashchange', navigate)
  }, [])

  const current = navigation.find(item => item.id === page)!
  return <ToastProvider>
    <div className="app-shell">
      <Sidebar current={page} />
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumbs"><span>Рабочее пространство</span><ChevronRight size={13} /><strong>{current.label}</strong></div>
          <div className={`health-status ${health.data === 'ok' ? 'online' : ''}`}>
            <span />{health.loading ? 'Проверяем API' : health.data === 'ok' ? 'API подключён' : 'API недоступен'}
          </div>
        </header>
        <main id="main-content">
          {page === 'pipeline' && <PipelinePage onOpenDeal={setDealId} changedDeal={changedDeal} />}
          {page === 'analytics' && <Suspense fallback={<Loading />}><AnalyticsPage /></Suspense>}
          {page === 'clients' && <ClientsPage onOpenDeal={setDealId} />}
          {page === 'integrations' && <IntegrationsPage onOpenDeal={setDealId} />}
        </main>
      </div>
    </div>
    {dealId !== null && <DealDrawer key={dealId} id={dealId} onClose={() => setDealId(null)} onDealChange={setChangedDeal} />}
  </ToastProvider>
}
