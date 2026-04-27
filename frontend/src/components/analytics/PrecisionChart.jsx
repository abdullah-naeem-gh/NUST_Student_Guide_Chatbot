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

export default function PrecisionChart({ data, colors }) {
  return (
    <ChartCard
      title="Precision@k by retrieval method"
      subtitle="X-axis: k values (1, 3, 5, 10) · Y-axis: Precision@k"
    >
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--rule2)" />
            <XAxis dataKey="k" label={{ value: 'k', position: 'insideBottom', offset: -6 }} />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v) => Number(v).toFixed(1)}
              label={{ value: 'Precision@k', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip formatter={(value) => Number(value).toFixed(4)} />
            <Legend verticalAlign="top" height={30} />
            <Line type="monotone" dataKey="Hybrid" stroke={colors.Hybrid} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="TFIDF" stroke={colors.TFIDF} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Simhash" stroke={colors.Simhash} strokeWidth={2.5} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="Minhash" stroke={colors.Minhash} strokeWidth={2.5} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  )
}
