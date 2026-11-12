import { BarChart3, LayoutPanelTop, Send, Sparkles, UsersRound } from 'lucide-react'

export const navigation = [
  { id: 'pipeline', label: 'Воронка продаж', icon: LayoutPanelTop },
  { id: 'analytics', label: 'Аналитика и прогнозы', icon: BarChart3 },
  { id: 'clients', label: 'Клиенты', icon: UsersRound },
  { id: 'integrations', label: 'Тест интеграций / Telegram', icon: Send },
] as const

export type Page = (typeof navigation)[number]['id']

export function Sidebar({ current }: { current: Page }) {
  return <aside className="sidebar">
    <a className="brand" href="#pipeline">
      <span className="brand-mark"><Sparkles size={21} /></span>
      <span>AI Sales <strong>CRM</strong></span>
    </a>
    <div className="nav-label">Рабочее пространство</div>
    <nav aria-label="Основная навигация">
      {navigation.map(({ id, label, icon: Icon }) => <a className={`nav-link ${current === id ? 'active' : ''}`}
        key={id} href={`#${id}`} aria-current={current === id ? 'page' : undefined}>
        <Icon size={17} /><span>{label}</span>
      </a>)}
    </nav>
    <div className="sidebar-footer">
      <span className="workspace-mark">S</span>
      <div><strong>Sales Workspace</strong><span>Локальный стенд</span></div>
    </div>
  </aside>
}
