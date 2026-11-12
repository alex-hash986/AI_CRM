import { CheckCircle2, CircleAlert, X } from 'lucide-react'
import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'

type ToastKind = 'success' | 'error'
type Notify = (text: string, kind?: ToastKind) => void
const ToastContext = createContext<Notify>(() => {})

export function useToast() {
  return useContext(ToastContext)
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<{ id: number; text: string; kind: ToastKind }[]>([])
  const nextId = useRef(0)
  const timers = useRef(new Map<number, number>())
  function remove(id: number) {
    window.clearTimeout(timers.current.get(id))
    timers.current.delete(id)
    setItems(previous => previous.filter(item => item.id !== id))
  }
  const notify: Notify = (text, kind = 'success') => {
    const id = nextId.current++
    setItems(previous => [...previous, { id, text, kind }])
    timers.current.set(id, window.setTimeout(() => remove(id), 5500))
  }

  useEffect(() => {
    const activeTimers = timers.current
    return () => activeTimers.forEach(timer => window.clearTimeout(timer))
  }, [])

  return <ToastContext.Provider value={notify}>
    {children}
    <div className="toast-region" aria-live="polite">
      {items.map(({ id, text, kind }) => <div className={`toast ${kind}`} key={id}>
        {kind === 'error' ? <CircleAlert size={18} /> : <CheckCircle2 size={18} />}
        <span>{text}</span>
        <button className="icon-button" aria-label="Закрыть уведомление" onClick={() => remove(id)}><X size={15} /></button>
      </div>)}
    </div>
  </ToastContext.Provider>
}
