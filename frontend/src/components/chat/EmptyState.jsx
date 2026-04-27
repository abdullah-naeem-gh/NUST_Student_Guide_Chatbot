const SUGGESTIONS = [
  { icon: '📊', text: 'What is the minimum GPA requirement?' },
  { icon: '📅', text: 'What is the attendance policy?' },
  { icon: '🔄', text: 'How many times can a course be repeated?' },
  { icon: '❌', text: 'What happens if a student fails a course?' },
]

export default function EmptyState({ onSelect }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      flex: 1,
      gap: 20,
      textAlign: 'center',
      padding: 32,
      minHeight: 240,
      fontFamily: 'var(--font-sans)',
    }}>
      <div style={{
        width: 48, height: 48, background: 'var(--accent)', borderRadius: 12,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
      </div>

      <div>
        <p style={{ fontWeight: 700, fontSize: 16, color: 'var(--ink)', marginBottom: 6 }}>NUST Guide</p>
        <p style={{ fontSize: 14, color: 'var(--ink3)', fontFamily: 'var(--font-serif)', fontStyle: 'italic' }}>
          Ask anything about academic policies
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%', maxWidth: 420 }}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s.text}
            type="button"
            onClick={() => onSelect(s.text)}
            className="suggestion-card"
            style={{
              padding: '10px 14px',
              borderRadius: 8,
              background: 'var(--paper)',
              border: '1.5px solid var(--rule)',
              textAlign: 'left',
              fontSize: 13.5,
              color: 'var(--ink2)',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <span>{s.icon}</span>
            {s.text}
          </button>
        ))}
      </div>
    </div>
  )
}
