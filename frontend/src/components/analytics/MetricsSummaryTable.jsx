import ChartCard from './ChartCard'

function fmt(value, digits = 4) {
  return Number(value).toFixed(digits)
}

export default function MetricsSummaryTable({ rows }) {
  return (
    <ChartCard title="Metrics summary by method" subtitle="Averages from benchmark experiment runs">
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, color: 'var(--ink)' }}>
          <thead>
            <tr style={{ background: 'var(--bg)' }}>
              {[
                'Method',
                'P@1',
                'P@3',
                'P@5',
                'P@10',
                'R@5',
                'MAP@5',
                'Latency (ms)',
                'Memory (MB)',
              ].map((header) => (
                <th
                  key={header}
                  style={{
                    textAlign: 'left',
                    padding: '8px 10px',
                    border: '1px solid var(--rule)',
                    fontWeight: 700,
                  }}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.method}>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)', fontWeight: 600 }}>{row.method}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.p1)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.p3)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.p5)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.p10)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.r5)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.map5)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.latencyMs, 3)}</td>
                <td style={{ padding: '8px 10px', border: '1px solid var(--rule)' }}>{fmt(row.memoryMb, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ChartCard>
  )
}
