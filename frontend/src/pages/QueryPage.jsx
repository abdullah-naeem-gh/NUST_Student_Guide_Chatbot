import { useEffect, useMemo } from 'react'
import Navbar from '../components/layout/Navbar'
import ChatPanel from '../components/chat/ChatPanel'
import EvidencePanel from '../components/evidence/EvidencePanel'
import useAppStore from '../store/appStore'
import { runQuery } from '../api/query'
import { getStatus } from '../api/status'
import { parseSourceFilesFromStatus, resolveHandbookFiles } from '../lib/handbooks'

/**
 * QueryPage — two-panel chat interface (60% chat / 40% evidence)
 */
export default function QueryPage() {
  const {
    messages,
    addMessage,
    updateMessage,
    activeResultId,
    isLoading,
    setLoading,
    setIndexStatus,
    selectedHandbookFile,
    setSelectedHandbookFile,
  } = useAppStore()

  useEffect(() => {
    getStatus()
      .then((s) => {
        setIndexStatus(s)
        const files = parseSourceFilesFromStatus(s)
        const { ug, pg } = resolveHandbookFiles(files)
        const state = useAppStore.getState()
        const cur = state.selectedHandbookFile
        const valid = typeof cur === 'string' && cur.length > 0 && files.includes(cur)
        if (valid) {
          return
        }
        if (ug || pg) {
          setSelectedHandbookFile(ug ?? pg ?? null)
        } else {
          setSelectedHandbookFile(files[0] ?? null)
        }
      })
      .catch(console.error)
  }, [setIndexStatus, setSelectedHandbookFile])

  const handleSend = async (query, method, k, generateAnswer) => {
    const userId = Date.now()
    const aiId = userId + 1

    addMessage({ id: userId, role: 'user', content: query, timestamp: new Date() })
    setLoading(true)

    try {
      const data = await runQuery(query, method, k, generateAnswer, selectedHandbookFile)

      const answerText =
        typeof data.answer === 'string' && data.answer.trim().length > 0
          ? data.answer
          : extractFallbackAnswer(data, method)

      addMessage({
        id: aiId,
        role: 'assistant',
        content: answerText,
        results: { method, results: data.results ?? data, query },
        timestamp: new Date(),
      })
    } catch (err) {
      addMessage({
        id: aiId,
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
        results: null,
        timestamp: new Date(),
      })
    } finally {
      setLoading(false)
    }
  }

  // The result object to pass to the evidence panel
  const activeResult = useMemo(() => {
    if (!activeResultId) {
      // Default to most recent AI message with results
      const last = [...messages].reverse().find(
        (m) => m.role === 'assistant' && m.results
      )
      return last?.results ?? null
    }
    const msg = messages.find((m) => m.id === activeResultId)
    return msg?.results ?? null
  }, [activeResultId, messages])

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg)' }}>
      <Navbar />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <div
          className="flex flex-col min-h-0 shrink-0"
          style={{ width: 420, minWidth: 320, maxWidth: 'min(420px, 44vw)' }}
        >
          <ChatPanel onSend={handleSend} />
        </div>

        <div className="flex flex-col flex-1 min-w-0 min-h-0" style={{ background: 'var(--bg)' }}>
          <EvidencePanel activeResult={activeResult} />
        </div>
      </div>
    </div>
  )
}

/** Fallback when LLM answer is not generated */
function extractFallbackAnswer(data, method) {
  try {
    const results = data.results ?? data
    const chunks = method === 'all'
      ? (results.minhash?.chunks ?? results.simhash?.chunks ?? results.tfidf?.chunks ?? [])
      : (results[method]?.chunks ?? [])
    if (chunks.length === 0) return 'No relevant sections found for that query.'
    return `Found ${chunks.length} relevant section${chunks.length > 1 ? 's' : ''} in the handbook. See the sources panel for details.`
  } catch {
    return 'Retrieval complete. See sources panel for results.'
  }
}
