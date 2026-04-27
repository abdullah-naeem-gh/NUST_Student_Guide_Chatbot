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

function SmallSensitivityChart({ title, subtitle, data, color, xLabel, yLabel }) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      <div style={{ width: '100%', height: 250 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 12, right: 16, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--rule2)" />
            <XAxis dataKey="x" label={{ value: xLabel, position: 'insideBottom', offset: -6 }} />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v) => Number(v).toFixed(1)}
              label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
            />
            <Tooltip formatter={(value) => Number(value).toFixed(4)} />
            <Legend />
            <Line type="monotone" dataKey="value" name={yLabel} stroke={color} strokeWidth={2.5} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  )
}

export default function ParameterSensitivityCharts({ data, colors }) {
  return (
    <section>
      <h2 style={{ margin: '0 0 10px', fontSize: 18, fontWeight: 700, color: 'var(--ink)' }}>
        Parameter sensitivity
      </h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 12,
        }}
      >
        <SmallSensitivityChart
          title="MinHash sensitivity"
          subtitle="Mean Recall@5 vs NUM_PERM"
          data={data.minhash}
          color={colors.Minhash}
          xLabel="NUM_PERM"
          yLabel="Recall@5"
        />
        <SmallSensitivityChart
          title="LSH sensitivity"
          subtitle="Mean Recall@5 vs NUM_BANDS"
          data={data.lsh}
          color={colors.Hybrid}
          xLabel="NUM_BANDS"
          yLabel="Recall@5"
        />
        <SmallSensitivityChart
          title="SimHash sensitivity"
          subtitle="Mean Precision@5 vs Hamming threshold"
          data={data.simhash}
          color={colors.Simhash}
          xLabel="Threshold"
          yLabel="Precision@5"
        />
      </div>
    </section>
  )
}
