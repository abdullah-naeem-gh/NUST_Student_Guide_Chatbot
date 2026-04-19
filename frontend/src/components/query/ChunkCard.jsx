import { useState } from 'react'

/**
 * ChunkCard — compact source card for the evidence panel
 * @param {Object} props
 * @param {Object} props.chunk - Retrieved chunk data
 * @param {boolean} props.isShared - Appears in multiple methods
 * @param {boolean} props.isInAll - Appears in all 3 methods
 * @param {boolean} props.isActive - Currently active page in PDF viewer
 * @param {Function} props.onPageClick - (pageNum) => void
 */
export default function ChunkCard({ chunk, isShared, isInAll, isActive, onPageClick }) {
  const [expanded, setExpanded] = useState(false)
  const { text, score, highlight_spans, section_title, page_start, page_end } = chunk

  const renderText = () => {
    if (!highlight_spans?.length) return text

    const sorted = [...highlight_spans].sort((a, b) => a[0] - b[0])
    const parts = []
    let last = 0

    sorted.forEach(([start, end], i) => {
      if (start > last) parts.push(text.slice(last, start))
      parts.push(
        <mark key={i} className="chunk-highlight">{text.slice(start, end)}</mark>
      )
      last = end
    })

    if (last < text.length) parts.push(text.slice(last))
    return parts
  }

  const pageLabel = page_end > page_start
    ? `pp. ${page_start}–${page_end}`
    : `p. ${page_start}`

  return (
    <div
      className="rounded-xl transition-all"
      style={{
        background: isActive ? 'rgba(255,255,255,0.09)' : 'rgba(255,255,255,0.04)',
        border: isActive
          ? '1px solid rgba(255,255,255,0.2)'
          : '1px solid rgba(255,255,255,0.08)',
        padding: '14px 16px',
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <p
            className="text-xs font-semibold truncate"
            style={{ color: 'rgba(255,255,255,0.85)' }}
            title={section_title}
          >
            {section_title || 'General Policy'}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <button
              onClick={() => onPageClick?.(page_start)}
              className="text-xs font-medium transition-colors"
              style={{ color: isActive ? '#fff' : 'rgba(255,255,255,0.4)' }}
              title="Jump to page in PDF"
            >
              {pageLabel}
            </button>
            {isInAll && (
              <span
                className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(52,211,153,0.15)', color: '#6ee7b7', border: '1px solid rgba(52,211,153,0.2)' }}
              >
                ✓ All methods
              </span>
            )}
            {isShared && !isInAll && (
              <span
                className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                style={{ background: 'rgba(255,255,255,0.08)', color: 'rgba(255,255,255,0.4)' }}
              >
                overlap
              </span>
            )}
          </div>
        </div>

        <span
          className="text-[10px] font-medium shrink-0"
          style={{ color: 'rgba(255,255,255,0.3)' }}
        >
          {score.toFixed(3)}
        </span>
      </div>

      {/* Text */}
      <p
        className="text-xs leading-relaxed cursor-pointer"
        style={{
          color: 'rgba(255,255,255,0.6)',
          display: '-webkit-box',
          WebkitLineClamp: expanded ? 'unset' : 4,
          WebkitBoxOrient: 'vertical',
          overflow: expanded ? 'visible' : 'hidden',
        }}
        onClick={() => setExpanded((v) => !v)}
      >
        {renderText()}
      </p>
    </div>
  )
}
