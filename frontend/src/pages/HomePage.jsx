import { useEffect, useState } from 'react'
import { ping } from '../api/ping'

/**
 * Placeholder home: verifies the UI can reach GET /ping through src/api.
 */
export default function HomePage() {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ping()
      .then((data) => {
        if (!cancelled) {
          setPayload(data)
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err?.message || 'Request failed')
          setPayload(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-screen bg-[var(--color-primary)] px-6 py-10 text-[var(--color-text)]">
      <div className="mx-auto max-w-2xl">
        <h1 className="mb-2 text-2xl font-semibold tracking-tight">
          Academic Policy QA
        </h1>
        <p className="mb-6 text-sm text-slate-400">
          Phase 0 — backend connectivity via{' '}
          <code className="rounded bg-[var(--color-surface)] px-1.5 py-0.5 text-xs">
            GET /ping
          </code>
        </p>

        {loading && (
          <p className="text-sm text-slate-400" role="status">
            Contacting API…
          </p>
        )}

        {error && (
          <pre
            className="overflow-x-auto rounded-lg border border-red-500/40 bg-red-950/40 p-4 text-left text-sm text-red-200"
            role="alert"
          >
            {error}
          </pre>
        )}

        {payload && !error && (
          <pre className="overflow-x-auto rounded-lg border border-slate-700 bg-[var(--color-surface)] p-4 text-left text-sm">
            {JSON.stringify(payload, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}
