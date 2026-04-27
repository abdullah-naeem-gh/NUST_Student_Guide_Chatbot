import { useEffect, useMemo, useState } from 'react'
import Navbar from '../components/layout/Navbar'
import LandingPage from './LandingPage'
import ChatPanel from '../components/chat/ChatPanel'
import EvidencePanel from '../components/evidence/EvidencePanel'
import useAppStore from '../store/appStore'
import { runQuery } from '../api/query'
import { getStatus } from '../api/status'
import { parseSourceFilesFromStatus, resolveHandbookFiles } from '../lib/handbooks'

export default function QueryPage({ initialScreen = 'landing' }) {
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

  const [screen, setScreen] = useState(initialScreen)
  const [initialQuery, setInitialQuery] = useState('')
  const [evidenceOpen, setEvidenceOpen] = useState(true)

  useEffect(() => {
    getStatus()
      .then((s) => {
        setIndexStatus(s)
        const files = parseSourceFilesFromStatus(s)
        const { ug, pg } = resolveHandbookFiles(files)
        const state = useAppStore.getState()
        const cur = state.selectedHandbookFile
        const valid = typeof cur === 'string' && cur.length > 0 && files.includes(cur)
        if (!valid && (ug || pg)) {
          setSelectedHandbookFile(ug ?? pg ?? null)
        } else if (!valid) {
          setSelectedHandbookFile(files[0] ?? null)
        }
      })
      .catch(console.error)
  }, [setIndexStatus, setSelectedHandbookFile])

  const handleSend = async (query, method, k, generateAnswer) => {
    // Switch to chat view on first send
    setScreen('chat')

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

  const handleAsk = (q) => {
    setInitialQuery(q)
    setScreen('chat')
    // Send immediately
    handleSend(q, 'tfidf', 5, true)
  }

  const handleNavigate = (s) => {
    setScreen(s)
    if (s === 'landing') setInitialQuery('')
  }

  const activeResult = useMemo(() => {
    if (!activeResultId) {
      const last = [...messages].reverse().find((m) => m.role === 'assistant' && m.results)
      return last?.results ?? null
    }
    const msg = messages.find((m) => m.id === activeResultId)
    return msg?.results ?? null
  }, [activeResultId, messages])

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg)' }}>
      <Navbar screen={screen} onNavigate={handleNavigate} />

      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {screen === 'landing' ? (
          <LandingPage onAsk={handleAsk} />
        ) : (
          <>
            {/* Chat column */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
              flexShrink: 0,
              width: evidenceOpen ? 460 : '100%',
              minWidth: 320,
              maxWidth: evidenceOpen ? 'min(460px, 50vw)' : '100%',
              transition: 'width 0.2s ease, max-width 0.2s ease',
            }}>
              <ChatPanel onSend={handleSend} evidenceOpen={evidenceOpen} setEvidenceOpen={setEvidenceOpen} />
            </div>

            {/* Evidence panel */}
            {evidenceOpen && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, minHeight: 0, animation: 'fadeIn 0.2s ease both' }}>
                <EvidencePanel activeResult={activeResult} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

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
