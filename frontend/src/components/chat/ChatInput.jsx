import { useState, useRef, useEffect } from 'react'

const RETRIEVAL_METHODS = [
  { id: 'hybrid', label: 'Hybrid', desc: 'Semantic + keyword' },
  { id: 'minhash', label: 'MinHash', desc: 'Locality-sensitive hashing' },
  { id: 'simhash', label: 'SimHash', desc: 'Similarity fingerprinting' },
  { id: 'tfidf', label: 'TF-IDF', desc: 'Term frequency weighting (recommended)' },
  { id: 'all', label: 'Compare All', desc: 'Run all methods side-by-side' },
]

export default function ChatInput({
  onSend,
  isLoading,
  method,
  setMethod,
  k,
  setK,
  generateAnswer,
  setGenerateAnswer,
}) {
  const [query, setQuery] = useState('')
  const [methodPickerOpen, setMethodPickerOpen] = useState(false)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [query])

  const handleSubmit = () => {
    if (!query.trim() || isLoading) return
    onSend(query.trim(), method, k, generateAnswer)
    setQuery('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const currentMethod = RETRIEVAL_METHODS.find((m) => m.id === method) ?? RETRIEVAL_METHODS[0]

  return (
    <div
      className="chat-input-area"
      style={{
        flexShrink: 0,
        padding: '12px 20px 16px',
        background: 'var(--paper)',
        borderTop: '1px solid var(--rule)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Close method picker on outside click */}
      {methodPickerOpen && (
        <div
          onClick={() => setMethodPickerOpen(false)}
          style={{ position: 'fixed', inset: 0, zIndex: 49 }}
        />
      )}

      <div
        className="input-border"
        style={{
          background: 'var(--bg)',
          border: '1.5px solid var(--rule)',
          borderRadius: 14,
          position: 'relative',
          transition: 'border-color 0.15s',
        }}
      >
        {/* Method dropdown */}
        {methodPickerOpen && (
          <div style={{
            position: 'absolute',
            bottom: 'calc(100% + 8px)',
            left: 0,
            background: 'var(--paper)',
            border: '1px solid var(--rule)',
            borderRadius: 12,
            boxShadow: '0 8px 30px oklch(0% 0 0 / 0.12)',
            padding: 8,
            zIndex: 50,
            minWidth: 280,
          }}>
            {RETRIEVAL_METHODS.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => { setMethod(m.id); setMethodPickerOpen(false) }}
                className="method-item"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: 8,
                  textAlign: 'left',
                  background: method === m.id ? 'var(--accent-bg)' : 'transparent',
                  transition: 'background 0.1s',
                  border: 'none',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                    background: method === m.id ? 'var(--accent)' : 'var(--rule)',
                  }} />
                  <span style={{ fontSize: 13, fontWeight: 600, color: method === m.id ? 'var(--accent)' : 'var(--ink)' }}>
                    {m.label}
                  </span>
                </div>
                <span style={{ fontSize: 11, color: 'var(--ink3)' }}>{m.desc}</span>
              </button>
            ))}
          </div>
        )}

        {/* Textarea row */}
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, padding: '10px 12px' }}>
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about academic policies…"
            rows={1}
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              resize: 'none',
              fontSize: 14,
              lineHeight: 1.6,
              fontFamily: 'var(--font-sans)',
              color: 'var(--ink)',
              minHeight: 22,
              maxHeight: 120,
              overflow: 'auto',
            }}
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isLoading || !query.trim()}
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              flexShrink: 0,
              transition: 'background 0.15s',
              background: query.trim() && !isLoading ? 'var(--accent)' : 'var(--rule)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: 'none',
              cursor: query.trim() && !isLoading ? 'pointer' : 'not-allowed',
            }}
          >
            {isLoading ? (
              <div style={{
                width: 14, height: 14, border: '2px solid white', borderTopColor: 'transparent',
                borderRadius: '50%', animation: 'spin 0.8s linear infinite',
              }} />
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>

        {/* Toolbar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '6px 12px 9px',
          borderTop: '1px solid var(--rule2)',
        }}>
          {/* Method pill */}
          <button
            type="button"
            onClick={() => setMethodPickerOpen((v) => !v)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '4px 10px',
              borderRadius: 100,
              fontSize: 12,
              fontWeight: 600,
              transition: 'all 0.15s',
              cursor: 'pointer',
              background: methodPickerOpen ? 'var(--accent-bg)' : 'var(--rule2)',
              border: `1px solid ${methodPickerOpen ? 'var(--accent)' : 'transparent'}`,
              color: methodPickerOpen ? 'var(--accent)' : 'var(--ink2)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14" />
            </svg>
            {currentMethod.label}
            <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <polyline points={methodPickerOpen ? '6 15 12 9 18 15' : '6 9 12 15 18 9'} />
            </svg>
          </button>

          {/* k adjuster */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            borderRadius: 100,
            background: 'var(--rule2)',
            fontSize: 12,
            fontWeight: 600,
            color: 'var(--ink3)',
            fontFamily: 'var(--font-sans)',
          }}>
            <span>k =</span>
            <button
              type="button"
              onClick={() => setK(Math.max(1, k - 1))}
              style={{ color: 'var(--ink2)', fontSize: 15, lineHeight: 1, padding: '0 2px', background: 'none', border: 'none', cursor: 'pointer' }}
            >−</button>
            <span style={{ color: 'var(--accent)', minWidth: 14, textAlign: 'center' }}>{k}</span>
            <button
              type="button"
              onClick={() => setK(Math.min(20, k + 1))}
              style={{ color: 'var(--ink2)', fontSize: 15, lineHeight: 1, padding: '0 2px', background: 'none', border: 'none', cursor: 'pointer' }}
            >+</button>
          </div>

          {/* AI answer toggle */}
          <label style={{ display: 'flex', alignItems: 'center', gap: 5, cursor: 'pointer' }}>
            <div
              onClick={() => setGenerateAnswer((v) => !v)}
              style={{
                width: 28, height: 16, borderRadius: 10, flexShrink: 0,
                transition: 'background 0.2s', position: 'relative',
                background: generateAnswer ? 'var(--accent)' : 'var(--rule)',
                cursor: 'pointer',
              }}
            >
              <div style={{
                width: 10, height: 10, borderRadius: '50%', background: 'white',
                position: 'absolute', top: 3, transition: 'left 0.2s',
                left: generateAnswer ? 15 : 3,
              }} />
            </div>
            <span style={{ fontSize: 11.5, fontWeight: 500, color: 'var(--ink3)', fontFamily: 'var(--font-sans)' }}>
              AI answer
            </span>
          </label>

          <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--rule)', fontFamily: 'var(--font-mono)' }}>
            ↵ send
          </span>
        </div>
      </div>
    </div>
  )
}
