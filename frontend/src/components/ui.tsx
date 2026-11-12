import { AlertCircle, LoaderCircle, X } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'

export function Spinner() {
  return <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
}

export function Loading({ label = 'Загрузка данных…' }: { label?: string }) {
  return <div className="loading-state" role="status"><Spinner /> {label}</div>
}

export function LoadError({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-state" role="alert">
    <AlertCircle className="size-4 shrink-0" />
    <span>{message}</span>
    {retry && <button type="button" className="button button-secondary" onClick={retry}>Повторить</button>}
  </div>
}

export function Dialog({ title, children, onClose, drawer = false }: {
  title: string; children: ReactNode; onClose: () => void; drawer?: boolean
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    dialog?.showModal()
    return () => dialog?.close()
  }, [])
  return <dialog ref={ref} className={drawer ? 'dialog drawer' : 'dialog modal'} aria-label={title}
    onCancel={event => { event.preventDefault(); onClose() }}>
    <header className="dialog-header">
      <h2>{title}</h2>
      <button className="icon-button" type="button" onClick={onClose} aria-label="Закрыть"><X size={19} /></button>
    </header>
    {children}
  </dialog>
}
