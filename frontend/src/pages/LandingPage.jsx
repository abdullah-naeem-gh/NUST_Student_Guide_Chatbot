import { useState, useRef, useEffect } from 'react'

const SUGGESTIONS = [
  { icon: '📊', text: 'What is the minimum GPA requirement?' },
  { icon: '📅', text: 'What is the attendance policy?' },
  { icon: '🔄', text: 'How many times can a course be repeated?' },
  { icon: '❌', text: 'What happens if a student fails a course?' },
  { icon: '🏆', text: "What are the requirements for Dean's List?" },
  { icon: '📋', text: 'What is the grading scale at NUST?' },
]

export default function LandingPage({ onAsk }) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  const submit = () => {
    if (!query.trim()) return
    onAsk(query.trim())
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      {/* Hero */}
      <div
        className="hero-dots"
        style={{
          flex: '0 0 auto',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 24px 60px',
          minHeight: '45vh',
          textAlign: 'center',
        }}
      >
        <div className="tag" style={{ marginBottom: 20 }}>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" /></svg>
          NUST Student Handbook · AI-Powered
        </div>

        <h1 style={{
          fontSize: 'clamp(32px, 5vw, 52px)',
          fontWeight: 700,
          letterSpacing: '-0.03em',
          lineHeight: 1.1,
          color: 'var(--ink)',
          marginBottom: 16,
          fontFamily: 'var(--font-sans)',
        }}>
          Your Academic Policy Guide
        </h1>

        <p style={{
          fontSize: 17,
          color: 'var(--ink2)',
          lineHeight: 1.6,
          maxWidth: 520,
          marginBottom: 36,
          fontFamily: 'var(--font-serif)',
          fontStyle: 'italic',
        }}>
          Ask anything about NUST academic regulations, grading, attendance, and student policies.
        </p>

        {/* Search bar */}
        <div style={{ width: '100%', maxWidth: 620 }}>
          <div
            className="input-border"
            style={{
              display: 'flex',
              gap: 0,
              background: 'var(--paper)',
              border: '1.5px solid var(--rule)',
              borderRadius: 14,
              boxShadow: 'var(--shadow)',
              overflow: 'hidden',
              transition: 'border-color 0.15s',
            }}
            onFocusCapture={(e) => { e.currentTarget.style.borderColor = 'var(--accent)' }}
            onBlurCapture={(e) => { e.currentTarget.style.borderColor = 'var(--rule)' }}
          >
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
              placeholder="Ask about GPA, attendance, grading…"
              style={{
                flex: 1,
                padding: '16px 20px',
                fontSize: 15,
                border: 'none',
                outline: 'none',
                background: 'transparent',
                color: 'var(--ink)',
                fontFamily: 'var(--font-sans)',
              }}
            />
            <button
              onClick={submit}
              disabled={!query.trim()}
              style={{
                padding: '12px 20px',
                background: 'var(--accent)',
                color: 'white',
                fontSize: 14,
                fontWeight: 600,
                border: 'none',
                borderRadius: 10,
                margin: 4,
                transition: 'opacity 0.15s',
                flexShrink: 0,
                cursor: query.trim() ? 'pointer' : 'not-allowed',
                opacity: query.trim() ? 1 : 0.45,
                fontFamily: 'var(--font-sans)',
              }}
            >
              Ask →
            </button>
          </div>
        </div>
      </div>

      {/* Suggestion cards */}
      <div style={{ padding: '32px 24px 48px', maxWidth: 900, margin: '0 auto', width: '100%' }}>
        <p style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'var(--ink3)',
          marginBottom: 16,
          fontFamily: 'var(--font-sans)',
        }}>
          Common questions
        </p>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
          gap: 12,
        }}>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              className="suggestion-card"
              onClick={() => onAsk(s.text)}
              style={{
                textAlign: 'left',
                padding: '14px 16px',
                background: 'var(--paper)',
                border: '1.5px solid var(--rule)',
                borderRadius: 10,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                cursor: 'pointer',
                fontFamily: 'var(--font-sans)',
              }}
            >
              <span style={{ fontSize: 18, lineHeight: 1, flexShrink: 0 }}>{s.icon}</span>
              <span style={{ fontSize: 13.5, fontWeight: 500, color: 'var(--ink2)', lineHeight: 1.45 }}>{s.text}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
