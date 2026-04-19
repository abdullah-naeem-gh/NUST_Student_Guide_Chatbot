import useAppStore from '../../store/appStore'
import ChatMarkdown from './ChatMarkdown'

/**
 * @param {Object} props
 * @param {{ id, role, content, results, timestamp }} props.message
 */
export default function ChatMessage({ message }) {
  const { activeResultId, setActiveResultId, setEvidenceFocus } = useAppStore()
  const { id, role, content, results } = message
  const isActive = activeResultId === id

  const handleAssistantClick = () => {
    if (role === 'assistant' && results) setActiveResultId(id)
  }

  if (role === 'typing') {
    return (
      <div className="chat-message-enter">
        <div
          className="inline-flex items-center gap-1.5 px-4 py-3 rounded-sm border"
          style={{
            background: 'var(--bg)',
            borderColor: 'var(--rule)',
          }}
        >
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    )
  }

  if (role === 'user') {
    return (
      <div className="flex justify-end chat-message-enter">
        <div
          className="max-w-[78%] text-sm leading-relaxed px-4 py-3 rounded-sm border italic"
          style={{
            background: 'var(--bg)',
            borderColor: 'var(--rule)',
            color: 'var(--ink2)',
          }}
        >
          {content}
        </div>
      </div>
    )
  }

  const sourceChunks = getSourceChunks(results)

  return (
    <div className="chat-message-enter max-w-full">
      <div
        role={results ? 'button' : undefined}
        tabIndex={results ? 0 : undefined}
        onClick={handleAssistantClick}
        onKeyDown={(e) => {
          if (results && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault()
            handleAssistantClick()
          }
        }}
        className="rounded-sm transition-colors"
        style={{
          outline: isActive ? `1px solid var(--accent)` : 'none',
          cursor: results ? 'pointer' : 'default',
        }}
      >
        <div
          className="font-mono uppercase mb-2.5 text-[10px] tracking-[0.1em]"
          style={{ color: 'var(--accent)' }}
        >
          Answer
        </div>
        <div
          className="text-sm leading-[1.75] pl-4 border-l-2"
          style={{ borderLeftColor: 'var(--accent)', color: 'var(--ink)' }}
        >
          <ChatMarkdown>{content}</ChatMarkdown>
        </div>

        {sourceChunks.length > 0 && (
          <div
            className="mt-3.5 pt-3 flex items-center gap-2 flex-wrap border-t"
            style={{ borderColor: 'var(--rule)' }}
          >
            <span
              className="font-mono uppercase text-[10px] tracking-[0.08em] shrink-0"
              style={{ color: 'var(--ink3)' }}
            >
              Sources
            </span>
            {sourceChunks.map((chunk) => (
              <button
                key={chunk.chunk_id}
                type="button"
                className="font-mono text-[10.5px] px-2 py-0.5 rounded-[1px] border transition-colors"
                style={{
                  color: 'var(--accent)',
                  borderColor: 'currentColor',
                  background: 'transparent',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--accent)'
                  e.currentTarget.style.color = 'var(--paper)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                  e.currentTarget.style.color = 'var(--accent)'
                }}
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
