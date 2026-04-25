import { useEffect, useMemo, useRef, useState } from 'react'
import useAppStore from '../../store/appStore'
import PdfChunkViewer from './PdfChunkViewer'
import ChunkDrawer from './ChunkDrawer'

/**
 * Right column: document header, chunk nav, PDF (top), retrieved rows (bottom).
 * @param {Object} props
 * @param {Object|null} props.activeResult
 */
export default function EvidencePanel({ activeResult }) {
  const [activeMethod, setActiveMethod] = useState('hybrid')
  const [activeChunkIndex, setActiveChunkIndex] = useState(0)
  const [panelView, setPanelView] = useState('document')

  const { indexStatus, evidenceFocus, setEvidenceFocus, selectedHandbookFile } = useAppStore()

  const isAll = activeResult?.method === 'all'

  const chunks = useMemo(() => {
    if (!activeResult) return []
    const results = activeResult.results
    if (isAll) {
      return results[activeMethod]?.chunks ?? []
    }
    return results[activeResult.method]?.chunks ?? []
  }, [activeResult, activeMethod, isAll])

  const chunkIdKey = useMemo(() => chunks.map((c) => c.chunk_id).join('|'), [chunks])

  const chunksRef = useRef(chunks)
  chunksRef.current = chunks

  useEffect(() => {
    setActiveChunkIndex(0)
  }, [activeResult, activeMethod, chunkIdKey])

  useEffect(() => {
    if (!evidenceFocus) return
    const { chunkId, pageStart } = evidenceFocus
    if (!chunkId && pageStart == null) return

    const list = chunksRef.current
    let idx = chunkId ? list.findIndex((c) => c.chunk_id === chunkId) : -1
    if (idx < 0 && pageStart != null) {
      idx = list.findIndex((c) => Number(c.page_start) === Number(pageStart))
    }
    if (idx >= 0) {
      setActiveChunkIndex(idx)
      setPanelView('document')
    }
    setEvidenceFocus(null)
  }, [evidenceFocus, chunkIdKey, setEvidenceFocus])

  const latencies = useMemo(() => {
    if (!activeResult || !isAll) return {}
    const r = activeResult.results
    return {
      hybrid: r.hybrid?.latency_ms,
      minhash: r.minhash?.latency_ms,
      simhash: r.simhash?.latency_ms,
      tfidf: r.tfidf?.latency_ms,
    }
  }, [activeResult, isAll])

  const methodLabel = useMemo(() => {
    if (!activeResult) return '—'
    const LABELS = { hybrid: 'Hybrid', minhash: 'MinHash', simhash: 'SimHash', tfidf: 'TF-IDF' }
    if (isAll) return LABELS[activeMethod] ?? activeMethod
    return LABELS[activeResult.method] ?? activeResult.method
  }, [activeResult, activeMethod, isAll])

  const filename =
    fileBasename(selectedHandbookFile || indexStatus.source_file) || 'No PDF indexed yet'

  const n = chunks.length
  const safeIndex = n ? Math.max(0, Math.min(activeChunkIndex, n - 1)) : 0
  const canPrev = n > 0 && safeIndex > 0
  const canNext = n > 0 && safeIndex < n - 1

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden" style={{ background: 'var(--bg)' }}>
      <div
        className="h-10 shrink-0 flex items-center gap-4 px-8 border-b"
        style={{ background: 'var(--paper)', borderColor: 'var(--rule)' }}
      >
        <div
          className="font-mono text-[10.5px] min-w-0 flex-1 truncate"
          style={{ color: 'var(--ink2)' }}
          title={filename}
        >
          {filename}
        </div>
        <div className="flex h-full items-stretch shrink-0">
          <ViewTab active={panelView === 'document'} onClick={() => setPanelView('document')}>
            Document
          </ViewTab>
          <ViewTab active={panelView === 'chunks'} onClick={() => setPanelView('chunks')}>
            Chunks
          </ViewTab>
        </div>
      </div>

      {isAll && activeResult && (
        <div
          className="flex items-center gap-2 px-8 py-1.5 border-b shrink-0 flex-wrap"
          style={{ background: 'var(--paper)', borderColor: 'var(--rule)' }}
        >
          <span className="font-mono text-[10px] uppercase tracking-wide" style={{ color: 'var(--ink3)' }}>
            Method
          </span>
          {(['hybrid', 'minhash', 'simhash', 'tfidf']).map((key) => {
            const on = activeMethod === key
            const LABELS = { hybrid: 'Hybrid', minhash: 'MinHash', simhash: 'SimHash', tfidf: 'TF-IDF' }
            const label = LABELS[key] ?? key
            const ms = latencies[key]
            return (
              <button
                key={key}
                type="button"
                onClick={() => setActiveMethod(key)}
                className="font-mono text-[10px] px-2 py-1 rounded-[1px] border transition-colors"
                style={{
                  color: on ? 'var(--accent)' : 'var(--ink3)',
                  borderColor: on ? 'var(--accent)' : 'transparent',
                  background: on ? 'var(--hi2)' : 'transparent',
                }}
              >
                {label}
                {ms !== undefined && (
                  <span style={{ color: 'var(--ink3)', marginLeft: 6 }}>
                    {ms < 1 ? '<1' : Math.round(ms)}ms
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      {activeResult && n > 0 && (
        <div
          className="flex items-center justify-between px-8 py-2 border-b shrink-0"
          style={{ background: 'var(--paper)', borderColor: 'var(--rule)' }}
        >
          <div className="font-mono text-[10.5px]" style={{ color: 'var(--ink3)' }}>
            Chunk{' '}
            <strong style={{ color: 'var(--accent)', fontWeight: 400 }}>{safeIndex + 1}</strong> of{' '}
            <strong style={{ color: 'var(--accent)', fontWeight: 400 }}>{n}</strong>
            &nbsp;·&nbsp; {methodLabel} retrieval
          </div>
          <div className="flex gap-1">
            <NavArrow disabled={!canPrev} onClick={() => canPrev && setActiveChunkIndex(safeIndex - 1)} title="Previous">
              ‹
            </NavArrow>
            <NavArrow disabled={!canNext} onClick={() => canNext && setActiveChunkIndex(safeIndex + 1)} title="Next">
              ›
            </NavArrow>
          </div>
        </div>
      )}

      {!activeResult && <EmptyEvidence />}

      {activeResult && n === 0 && (
        <p className="text-center font-mono text-[11px] py-16" style={{ color: 'var(--ink3)' }}>
          No results for this method
        </p>
      )}

      {activeResult && n > 0 && panelView === 'document' && (
        <>
          <PdfChunkViewer
            chunks={chunks}
            activeChunkIndex={activeChunkIndex}
            pdfFilename={selectedHandbookFile}
            className="min-h-0 flex-1"
          />
          <ChunkDrawer
            chunks={chunks}
            activeChunkIndex={activeChunkIndex}
            onSelectChunk={setActiveChunkIndex}
            variant="drawer"
          />
        </>
      )}

      {activeResult && n > 0 && panelView === 'chunks' && (
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
          <ChunkDrawer
            chunks={chunks}
            activeChunkIndex={activeChunkIndex}
            onSelectChunk={(i) => {
              setActiveChunkIndex(i)
              setPanelView('document')
            }}
            variant="full"
          />
        </div>
      )}
    </div>
  )
}

function ViewTab({ children, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="font-mono uppercase px-3.5 h-full -mb-px border-b-2 transition-colors text-[10px] tracking-[0.08em]"
      style={{
        color: active ? 'var(--accent)' : 'var(--ink3)',
        borderBottomColor: active ? 'var(--accent)' : 'transparent',
        background: 'none',
        borderTop: 'none',
        borderLeft: 'none',
        borderRight: 'none',
      }}
    >
      {children}
    </button>
  )
}

function NavArrow({ children, disabled, onClick, title }) {
  return (
    <button
      type="button"
      title={title}
      disabled={disabled}
      onClick={onClick}
      className="font-mono w-[26px] h-[22px] grid place-items-center rounded-[1px] border transition-colors text-[11px] disabled:opacity-50"
      style={{
        borderColor: 'var(--rule)',
        color: disabled ? 'var(--ink3)' : 'var(--ink3)',
        background: 'transparent',
      }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.borderColor = 'var(--accent)'
          e.currentTarget.style.color = 'var(--accent)'
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--rule)'
        e.currentTarget.style.color = 'var(--ink3)'
      }}
    >
      {children}
    </button>
  )
}

function EmptyEvidence() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-3 px-8 py-12">
      <svg
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ color: 'var(--rule)' }}
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
      <p className="font-mono text-[11px] text-center" style={{ color: 'var(--ink3)' }}>
        Run a query to see sources and the handbook PDF
      </p>
    </div>
  )
}

function fileBasename(path) {
  if (!path || typeof path !== 'string') return ''
  const parts = path.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] || ''
}
