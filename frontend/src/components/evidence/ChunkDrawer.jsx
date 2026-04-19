/**
 * Retrieved chunk rows (drawer or full-height list).
 * @param {Object} props
 * @param {any[]} props.chunks
 * @param {number} props.activeChunkIndex
 * @param {function} props.onSelectChunk - (index: number) => void
 * @param {'drawer'|'full'} [props.variant]
 */
export default function ChunkDrawer({
  chunks,
  activeChunkIndex,
  onSelectChunk,
  variant = 'drawer',
}) {
  const isDrawer = variant === 'drawer'

  return (
    <div
      className="flex flex-col border-t min-h-0 overflow-hidden"
      style={{
        borderColor: 'var(--rule)',
        background: 'var(--paper)',
        flexShrink: 0,
        ...(isDrawer ? { height: 200 } : { flex: 1, minHeight: 0 }),
      }}
    >
      <div
        className="sticky top-0 z-[1] border-b px-8 py-2 font-mono uppercase text-[9.5px] tracking-[0.14em] shrink-0"
        style={{ background: 'var(--paper)', borderColor: 'var(--rule)', color: 'var(--ink3)' }}
      >
        Retrieved chunks — {chunks.length} results
      </div>
      <div className="overflow-y-auto min-h-0 flex-1">
        {chunks.map((chunk, i) => (
          <ChunkRow
            key={`${chunk.chunk_id}-${i}`}
            chunk={chunk}
            isActive={activeChunkIndex === i}
            onRowClick={() => onSelectChunk(i)}
            onViewClick={(e) => {
              e.stopPropagation()
              onSelectChunk(i)
            }}
          />
        ))}
      </div>
    </div>
  )
}

function ChunkRow({ chunk, isActive, onRowClick, onViewClick }) {
  const { text, score, page_start, page_end } = chunk
  const pages =
    page_end != null && page_end > page_start ? `pp. ${page_start}–${page_end}` : `p. ${page_start}`

  const snippet = (text || '').replace(/\s+/g, ' ').trim()
  const short = snippet.length > 140 ? `${snippet.slice(0, 140)}…` : snippet

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onRowClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onRowClick()
        }
      }}
      className="flex items-baseline gap-0 px-8 py-3 border-b cursor-pointer transition-colors font-serif text-[12.5px]"
      style={{
        borderColor: 'var(--rule)',
        background: isActive ? 'var(--hi2)' : 'transparent',
      }}
    >
      <div
        className="w-[52px] shrink-0 font-mono text-[11px] font-light"
        style={{ color: 'var(--accent)' }}
      >
        {typeof score === 'number' ? score.toFixed(3) : '—'}
      </div>
      <div className="w-[88px] shrink-0 font-mono text-[10.5px]" style={{ color: 'var(--ink3)' }}>
        {pages}
      </div>
      <div
        className="flex-1 min-w-0 overflow-hidden text-ellipsis whitespace-nowrap leading-snug"
        style={{ color: 'var(--ink2)' }}
        title={snippet}
      >
        {short}
      </div>
      <button
        type="button"
        className="shrink-0 ml-4 font-mono text-[10px] border-none bg-transparent cursor-pointer tracking-wide"
        style={{ color: 'var(--ink3)' }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = 'var(--accent)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = 'var(--ink3)'
        }}
        onClick={onViewClick}
      >
        ↑ view
      </button>
    </div>
  )
}
