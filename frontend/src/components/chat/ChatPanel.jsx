import { useEffect, useRef, useState } from 'react'
import useAppStore from '../../store/appStore'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import EmptyState from './EmptyState'

const RETRIEVAL_METHODS = [
  { id: 'hybrid', label: 'Hybrid' },
  { id: 'minhash', label: 'MinHash' },
  { id: 'simhash', label: 'SimHash' },
  { id: 'tfidf', label: 'TF-IDF' },
  { id: 'all', label: 'Compare All' },
]

export default function ChatPanel({ onSend, evidenceOpen, setEvidenceOpen }) {
  const { messages, isLoading } = useAppStore()
  const bottomRef = useRef(null)

  const [method, setMethod] = useState('tfidf')
  const [k, setK] = useState(5)
  const [generateAnswer, setGenerateAnswer] = useState(true)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const methodLabel = RETRIEVAL_METHODS.find((m) => m.id === method)?.label ?? method

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        minHeight: 0,
        background: 'var(--bg)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Sub-header */}
      <div style={{
        height: 40,
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        borderBottom: '1px solid var(--rule)',
        background: 'var(--paper)',
        gap: 12,
      }}>
        <span style={{
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: 'var(--ink3)',
          fontFamily: 'var(--font-sans)',
        }}>
          {methodLabel} retrieval · k={k}
        </span>
        <div style={{ flex: 1 }} />
        <button
          type="button"
          onClick={() => setEvidenceOpen((v) => !v)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            fontWeight: 600,
            color: evidenceOpen ? 'var(--accent)' : 'var(--ink3)',
            padding: '4px 10px',
            borderRadius: 6,
            border: `1px solid ${evidenceOpen ? 'var(--accent)' : 'var(--rule)'}`,
            background: evidenceOpen ? 'var(--accent-bg)' : 'transparent',
            transition: 'all 0.15s',
            cursor: 'pointer',
            fontFamily: 'var(--font-sans)',
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          {evidenceOpen ? 'Hide sources' : 'Show sources'}
        </button>
      </div>

      {/* Messages */}
      <div
        className="messages-scroll"
        style={{ flex: 1, overflowY: 'auto', padding: '28px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}
      >
        {messages.length === 0 && !isLoading ? (
          <EmptyState onSelect={(s) => onSend(s, method, k, generateAnswer)} />
        ) : (
          <>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isLoading && <ChatMessage message={{ id: 'typing', role: 'typing' }} />}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={onSend}
        isLoading={isLoading}
        method={method}
        setMethod={setMethod}
        k={k}
        setK={setK}
        generateAnswer={generateAnswer}
        setGenerateAnswer={setGenerateAnswer}
      />
    </div>
  )
}
