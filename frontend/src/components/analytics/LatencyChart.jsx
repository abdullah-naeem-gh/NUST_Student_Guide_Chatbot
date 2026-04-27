import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import ChartCard from './ChartCard'

export default function LatencyChart({ data }) {
  return (
    <ChartCard
      title="Mean query latency by method"
      subtitle="X-axis: retrieval methods · Y-axis: latency (ms)"
    >
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--rule2)" />
            <XAxis dataKey="method" label={{ value: 'Method', position: 'insideBottom', offset: -6 }} />
            <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `${Number(value).toFixed(3)} ms`} />
            <Legend />
            <Bar dataKey="latencyMs" name="Mean Latency (ms)" radius={[6, 6, 0, 0]}>
              {data.map((row) => (
                <Cell key={row.method} fill={row.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  )
}
