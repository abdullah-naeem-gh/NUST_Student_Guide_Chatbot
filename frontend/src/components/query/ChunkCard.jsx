/**
 * ChunkCard — Displays a single retrieved chunk with highlights
 * @param {Object} props
 * @param {Object} props.chunk - Chunk data (text, score, highlights)
 * @param {boolean} props.isShared - Whether this chunk appears in other methods
 */
export default function ChunkCard({ chunk, isShared }) {
  const { text, score, highlight_spans } = chunk

  const renderHighlightedText = () => {
    if (!highlight_spans || highlight_spans.length === 0) {
      return text
    }

    const result = []
    let lastIndex = 0

    // Sort spans by start index
    const sortedSpans = [...highlight_spans].sort((a, b) => a[0] - b[0])

    sortedSpans.forEach((span, i) => {
      const [start, end] = span
      // Add text before the span
      if (start > lastIndex) {
        result.push(text.substring(lastIndex, start))
      }
      // Add the highlighted span
      result.push(
        <span key={i} className="bg-amber/30 text-amber font-medium rounded-sm px-0.5">
          {text.substring(start, end)}
        </span>
      )
      lastIndex = end
    })

    // Add remaining text
    if (lastIndex < text.length) {
      result.push(text.substring(lastIndex))
    }

    return result
  }

  return (
    <div className={`p-4 rounded-xl border transition-all ${
      isShared 
        ? 'bg-navy-800/80 border-electric/40 shadow-[0_0_15px_rgba(59,130,246,0.1)]' 
        : 'bg-navy-800/40 border-navy-700 hover:border-navy-600'
    }`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono font-bold text-slate-500 bg-navy-900 px-1.5 py-0.5 rounded border border-navy-700">
            PAGE {chunk.page_start}{chunk.page_end > chunk.page_start ? `-${chunk.page_end}` : ''}
          </span>
          {isShared && (
            <span className="text-[10px] font-mono font-bold text-electric bg-electric/10 px-1.5 py-0.5 rounded border border-electric/20 uppercase">
              Overlap
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-mono text-slate-500 uppercase">Score</span>
          <span className="text-xs font-mono font-bold text-white">
            {score.toFixed(4)}
          </span>
        </div>
      </div>

      <div className="text-sm text-slate-300 leading-relaxed font-sans line-clamp-6 hover:line-clamp-none transition-all">
        {renderHighlightedText()}
      </div>

      <div className="mt-3 flex justify-between items-center border-t border-navy-700/50 pt-3">
        <span className="text-[9px] font-mono text-slate-500 truncate max-w-[200px]">
          {chunk.section_title || 'General Policy'}
        </span>
        <button className="text-[10px] font-mono text-electric hover:underline uppercase font-bold">
          View Context
        </button>
      </div>
    </div>
  )
}
