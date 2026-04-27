export default function ChartCard({ title, subtitle, children }) {
  return (
    <section
      style={{
        background: 'var(--paper)',
        border: '1px solid var(--rule)',
        borderRadius: 10,
        padding: 16,
        boxShadow: 'var(--shadow)',
      }}
    >
      <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: 'var(--ink)' }}>{title}</h2>
      {subtitle && (
        <p style={{ margin: '6px 0 12px', fontSize: 13, color: 'var(--ink3)' }}>
          {subtitle}
        </p>
      )}
      {children}
    </section>
  )
}
