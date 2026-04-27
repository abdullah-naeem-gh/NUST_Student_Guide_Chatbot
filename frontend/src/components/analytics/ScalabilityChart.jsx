import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import ChartCard from './ChartCard'

export default function ScalabilityChart({ data, colors }) {
  return (
    <ChartCard
      title="Scalability: latency vs corpus size"
      subtitle="X-axis: corpus scale (1x, 2x, 4x, 8x) · Y-axis: latency (ms)"
    >
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--rule2)" />
            <XAxis dataKey="scale" label={{ value: 'Corpus Size', position: 'insideBottom', offset: -6 }} />
            <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `${Number(value).toFixed(3)} ms`} />
            <Legend verticalAlign="top" height={30} />
            <Line type="monotone" dataKey="TFIDF" stroke={colors.TFIDF} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Minhash" stroke={colors.Minhash} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Simhash" stroke={colors.Simhash} strokeWidth={2.5} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  )
}
