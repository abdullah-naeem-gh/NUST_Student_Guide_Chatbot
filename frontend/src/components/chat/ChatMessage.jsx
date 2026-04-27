import useAppStore from '../../store/appStore'
import ChatMarkdown from './ChatMarkdown'

export default function ChatMessage({ message }) {
  const { activeResultId, setActiveResultId, setEvidenceFocus } = useAppStore()
  const { id, role, content, results } = message
  const isActive = activeResultId === id

  if (role === 'typing') {
    return (
      <div className="chat-message-enter" style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0' }}>
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    )
  }

  if (role === 'user') {
    return (
      <div className="chat-message-enter" style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div className="bubble-user">{content}</div>
      </div>
    )
  }

  const sourceChunks = getSourceChunks(results)

  return (
    <div
      className="chat-message-enter"
      style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 6 }}
    >
      {/* Assistant label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        <div style={{
          width: 22, height: 22, borderRadius: 6, background: 'var(--accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
          </svg>
        </div>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--ink3)', fontFamily: 'var(--font-sans)' }}>NUST Guide</span>
      </div>

      {/* Bubble */}
      <div
        className="bubble-assistant"
        role={results ? 'button' : undefined}
        tabIndex={results ? 0 : undefined}
        onClick={() => { if (results) setActiveResultId(id) }}
        onKeyDown={(e) => { if (results && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setActiveResultId(id) } }}
        style={{
          outline: isActive ? `2px solid var(--accent)` : 'none',
          cursor: results ? 'pointer' : 'default',
        }}
      >
        <ChatMarkdown>{content}</ChatMarkdown>
      </div>

      {/* Source chips */}
      {sourceChunks.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxWidth: '85%' }}>
          {sourceChunks.map((chunk) => (
            <button
              key={chunk.chunk_id}
              type="button"
              className="source-chip"
              onClick={(e) => {
                e.stopPropagation()
                setActiveResultId(id)
                setEvidenceFocus({
                  chunkId: chunk.chunk_id,
                  pageStart: chunk.page_start != null ? Number(chunk.page_start) : undefined,
                })
              }}
            >
              {pageLabel(chunk)}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function getSourceChunks(results) {
  if (!results?.results) return []
  const { method, results: r } = results
  if (method === 'all') {
    const list = r.minhash?.chunks ?? r.simhash?.chunks ?? r.tfidf?.chunks ?? []
    return list.slice(0, 8)
  }
  return (r[method]?.chunks ?? []).slice(0, 8)
}

function pageLabel(chunk) {
  const a = chunk.page_start
  const b = chunk.page_end
  if (b != null && b > a) return `pp. ${a}–${b}`
  return `p. ${a}`
}
