import { useEffect, useMemo, useState } from 'react'
import Navbar from '../components/layout/Navbar'
import { getExperiments } from '../api/experiments'
import {
  buildLatencySeries,
  buildMetricsSummary,
  buildPrecisionSeries,
  buildScalabilitySeries,
  buildSensitivitySeries,
  EXPERIMENT_METHODS,
} from '../lib/experiments'
import PrecisionChart from '../components/analytics/PrecisionChart'
import LatencyChart from '../components/analytics/LatencyChart'
import ScalabilityChart from '../components/analytics/ScalabilityChart'
import ParameterSensitivityCharts from '../components/analytics/ParameterSensitivityCharts'
import MetricsSummaryTable from '../components/analytics/MetricsSummaryTable'

const METHOD_COLORS = EXPERIMENT_METHODS.reduce((acc, method) => {
  acc[method.label] = method.color
  return acc
}, {})

export default function AnalyticsPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchData = async (refresh = false) => {
    setLoading(true)
    setError('')
    try {
      const experiments = await getExperiments({ refresh })
      setData(experiments)
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load experiments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(false)
  }, [])

  const precisionData = useMemo(() => buildPrecisionSeries(data), [data])
  const latencyData = useMemo(() => buildLatencySeries(data), [data])
  const scalabilityData = useMemo(() => buildScalabilitySeries(data), [data])
  const sensitivityData = useMemo(() => buildSensitivitySeries(data), [data])
  const summaryRows = useMemo(() => buildMetricsSummary(data), [data])

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>
      <Navbar screen="analytics" />

      <main style={{ flex: 1, overflowY: 'auto', padding: '24px 24px 36px' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', display: 'grid', gap: 14 }}>
          <header
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 12,
              background: 'var(--paper)',
              border: '1px solid var(--rule)',
              borderRadius: 10,
              padding: '14px 16px',
            }}
          >
            <div>
              <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: 'var(--ink)' }}>
                Analytics Dashboard
              </h1>
              <p style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--ink3)' }}>
                Source: GET /experiments · Generated at {data?.generated_at ?? '—'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => fetchData(false)}
              disabled={loading}
              style={{
                border: '1px solid var(--rule)',
                borderRadius: 8,
                background: loading ? 'var(--rule2)' : 'var(--paper)',
                color: 'var(--ink)',
                padding: '8px 12px',
                fontSize: 13,
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Refreshing…' : 'Reload'}
            </button>
          </header>

          {loading && (
            <div style={{ color: 'var(--ink2)', fontSize: 14, padding: '6px 2px' }}>
              Loading experiment data…
            </div>
          )}

          {!loading && error && (
            <div
              style={{
                background: '#fff1f2',
                border: '1px solid #fecdd3',
                color: '#9f1239',
                borderRadius: 10,
                padding: '12px 14px',
                fontSize: 14,
              }}
            >
              {error}
            </div>
          )}

          {!loading && !error && (
            <>
              <PrecisionChart data={precisionData} colors={METHOD_COLORS} />
              <LatencyChart data={latencyData} />
              <ScalabilityChart data={scalabilityData} colors={METHOD_COLORS} />
              <ParameterSensitivityCharts data={sensitivityData} colors={METHOD_COLORS} />
              <MetricsSummaryTable rows={summaryRows} />
            </>
          )}
        </div>
      </main>
    </div>
  )
}
