import { useEffect, useState } from 'react'
import { errorMessage } from '../api/apiClient'

export function useLoad<T>(loader: (signal: AbortSignal) => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [revision, setRevision] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    loader(controller.signal).then(
      value => {
        if (!controller.signal.aborted) {
          setData(value)
          setLoading(false)
        }
      },
      reason => {
        if (!controller.signal.aborted) {
          setData(null)
          setError(errorMessage(reason))
          setLoading(false)
        }
      },
    )
    return () => controller.abort()
  }, [loader, revision])

  return { data, loading, error, reload: () => setRevision(value => value + 1) }
}
