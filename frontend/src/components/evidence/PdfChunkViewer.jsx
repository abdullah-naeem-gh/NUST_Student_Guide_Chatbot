import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { SpecialZoomLevel, Viewer, Worker } from '@react-pdf-viewer/core'
import { pageNavigationPlugin } from '@react-pdf-viewer/page-navigation'
import { searchPlugin } from '@react-pdf-viewer/search'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.js?url'

import '@react-pdf-viewer/core/lib/styles/index.css'
import '@react-pdf-viewer/search/lib/styles/index.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * @param {any[]} chunks - current list of retrieved chunks
 * @param {number} activeChunkIndex
 * @param {string} [className]
 */
function normalizePhrase(s) {
  return s
    .replace(/\u2026/g, ' ')
    .replace(/…/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/[""'']/g, '')
    .trim()
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Match phrase even when the PDF inserts line breaks / odd spacing between words. */
function phraseToFlexibleRegExp(phrase) {
  const flat = normalizePhrase(phrase)
  if (!flat || flat.length < 3) {
    return null
  }
  const parts = flat.split(/\s+/).filter((w) => w.length > 0)
  if (parts.length === 0) {
    return null
  }
  if (parts.length === 1) {
    return new RegExp(escapeRegExp(parts[0]), 'gi')
  }
  const body = parts.map((w) => escapeRegExp(w)).join('\\s+')
  return new RegExp(body, 'gi')
}

/**
 * Search terms for @react-pdf-viewer/search: prefer RegExp with \\s+ between words
 * so PDF line breaks / spacing differences still match.
 */
/** Build search regexes from the selected chunk’s text only (not the user query). */
function buildHighlightTerms(chunk) {
  if (!chunk?.text) return []
  const text = chunk.text
  const phrases = []

  if (Array.isArray(chunk.highlight_spans) && chunk.highlight_spans.length) {
    for (const [s, e] of chunk.highlight_spans.slice(0, 5)) {
      const end = Math.min(e, s + 96)
      const phrase = normalizePhrase(text.slice(s, end))
      if (phrase.length > 3 && phrase.length < 160) {
        phrases.push(phrase)
      }
    }
  }

  const flat = normalizePhrase(text)
  const words = flat.split(/\s+/).filter((w) => w.length > 0)
  if (words.length >= 6) {
    phrases.push(words.slice(0, 10).join(' '))
  }
  if (words.length >= 3) {
    phrases.push(words.slice(0, 5).join(' '))
  }
  if (words.length >= 2) {
    phrases.push(words.slice(0, 3).join(' '))
  }

  const firstLine = text
    .split(/[\n.]/)
    .map((l) => l.trim())
    .find((l) => l.length > 10)
  if (firstLine) {
    const line = firstLine.length > 80 ? firstLine.slice(0, 80) : firstLine
    phrases.push(normalizePhrase(line))
  }

  const terms = []
  const seen = new Set()
  for (const p of phrases) {
    const re = phraseToFlexibleRegExp(p)
    if (!re) {
      continue
    }
    const key = re.toString()
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    terms.push(re)
    if (terms.length >= 10) {
      break
    }
  }

  if (terms.length === 0 && words.length) {
    const longest = [...words].sort((a, b) => b.length - a.length)[0]
    if (longest && longest.length >= 4) {
      terms.push(new RegExp(escapeRegExp(longest), 'gi'))
    }
  }

  return terms
}

/**
 * react-pdf-viewer with teal highlights; navigation lives in EvidencePanel.
 * @param {string|null} [pdfFilename] - served via GET /pdf?file=...
 */
export default function PdfChunkViewer({
  chunks,
  activeChunkIndex,
  pdfFilename = null,
  className = '',
}) {
  const [docReady, setDocReady] = useState(false)

  const fileUrl = useMemo(() => {
    const base = import.meta.env.DEV ? '/api/pdf' : `${API_BASE}/pdf`
    if (!pdfFilename) {
      return base
    }
    const q = `?file=${encodeURIComponent(pdfFilename)}`
    return `${base}${q}`
  }, [pdfFilename])

  const renderHighlights = useCallback((rProps) => (
    <div>
      {rProps.highlightAreas.map((area, idx) => (
        <div
          key={idx}
          style={{
            ...rProps.getCssProperties(area),
            position: 'absolute',
            zIndex: 1,
            background: 'rgba(29, 107, 94, 0.22)',
            outline: '1px solid rgba(29, 107, 94, 0.35)',
            pointerEvents: 'none',
          }}
        />
      ))}
    </div>
  ), [])

  const searchP = searchPlugin({ renderHighlights })
  const pageNavPlugin = pageNavigationPlugin()

  const searchRef = useRef(searchP)
  const pageNavRef = useRef(pageNavPlugin)
  const chunksRef = useRef(chunks)

  useEffect(() => {
    searchRef.current = searchP
    pageNavRef.current = pageNavPlugin
    chunksRef.current = chunks
  }, [searchP, pageNavPlugin, chunks])

  const n = chunks?.length ?? 0
  const safeIndex = n ? Math.max(0, Math.min(activeChunkIndex, n - 1)) : 0
  const chunk = n ? chunks[safeIndex] : null

  const highlightRunKey = useMemo(() => {
    if (!n || !chunks?.length) return ''
    const ids = chunks.map((c) => c.chunk_id).join('|')
    const c = chunks[safeIndex]
    const page = c?.page_start ?? ''
    return `${ids}#${safeIndex}#${page}`
  }, [n, chunks, safeIndex])

  useEffect(() => {
    if (!docReady || !n || !highlightRunKey) {
      return
    }
    const chunkNow = chunksRef.current[safeIndex]
    if (!chunkNow) {
      return
    }
    const { setTargetPages, clearHighlights, highlight } = searchRef.current
    const { jumpToPage } = pageNavRef.current

    const pStart = Math.max(1, Number(chunkNow.page_start) || 1)
    const pEnd = Math.max(pStart, Number(chunkNow.page_end) || pStart)
    const startIdx = pStart - 1
    const endIdx = pEnd - 1

    const terms = buildHighlightTerms(chunkNow)
    if (!terms.length) {
      return
    }

    let cancelled = false
    const sleep = (ms) => new Promise((r) => window.setTimeout(r, ms))

    const run = async () => {
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))

      const inChunkRange = (target) =>
        target.pageIndex >= startIdx && target.pageIndex <= endIdx

      setTargetPages(inChunkRange)
      clearHighlights()
      void jumpToPage(startIdx)

      const delays = [220, 450, 750, 1200]
      let anyMatch = false
      for (const ms of delays) {
        if (cancelled) {
          return
        }
        await sleep(ms)
        if (cancelled) {
          return
        }
        const matches = await highlight(terms)
        if (matches?.length) {
          anyMatch = true
          break
        }
      }

      if (!cancelled && !anyMatch) {
        setTargetPages(() => true)
        void jumpToPage(startIdx)
        await sleep(400)
        if (!cancelled) {
          await highlight(terms)
        }
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [docReady, highlightRunKey, n, safeIndex])

  const onDocLoad = useCallback(() => {
    setDocReady(true)
  }, [])

  useEffect(() => {
    const t = window.setTimeout(() => setDocReady(false), 0)
    return () => window.clearTimeout(t)
  }, [fileUrl])

  if (!n || !chunk) {
    return null
  }

  return (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        flex: 1,
        background: 'var(--bg)',
        borderTop: '1px solid var(--rule)',
      }}
    >
      <div
        style={{
          flex: 1,
          minHeight: 200,
          position: 'relative',
          background: 'var(--bg)',
        }}
      >
        <Worker workerUrl={workerUrl}>
          <div style={{ position: 'absolute', inset: 0, overflow: 'auto' }}>
            <Viewer
              key={fileUrl}
              fileUrl={fileUrl}
              defaultScale={SpecialZoomLevel.PageWidth}
              onDocumentLoad={onDocLoad}
              plugins={[searchP, pageNavPlugin]}
            />
          </div>
        </Worker>
      </div>
    </div>
  )
}
