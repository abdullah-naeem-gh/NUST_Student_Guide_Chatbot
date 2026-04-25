import { useEffect, useRef, useState } from 'react'
import useAppStore from '../../store/appStore'
import { parseSourceFilesFromStatus, resolveHandbookFiles } from '../../lib/handbooks'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import EmptyState from './EmptyState'

const METHODS = ['all', 'hybrid', 'minhash', 'simhash', 'tfidf']
const METHOD_LABELS = { all: 'All', hybrid: 'Hybrid', minhash: 'MinHash', simhash: 'SimHash', tfidf: 'TF-IDF' }

/**
 * Left column: retrieval strip, messages, input.
 * @param {Object} props
 * @param {Function} props.onSend - (query, method, k, generateAnswer) => void
 */
export default function ChatPanel({ onSend }) {
  const { messages, isLoading, indexStatus, selectedHandbookFile, setSelectedHandbookFile } =
    useAppStore()
  const bottomRef = useRef(null)

  const [method, setMethod] = useState('all')
  const [k, setK] = useState(5)
  const [generateAnswer, setGenerateAnswer] = useState(true)

  const { ug: ugFile, pg: pgFile } = resolveHandbookFiles(parseSourceFilesFromStatus(indexStatus))
  const showHandbookPicker = Boolean(ugFile || pgFile)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div
      className="flex flex-col h-full min-h-0 border-r"
      style={{ background: 'var(--paper)', borderColor: 'var(--rule)' }}
    >
      {showHandbookPicker && (
        <div
          className="flex items-center gap-0 shrink-0 border-b px-6 h-9"
          style={{ borderColor: 'var(--rule)' }}
        >
          <span
            className="font-mono uppercase mr-3.5 shrink-0"
            style={{
              fontSize: 10,
              letterSpacing: '0.12em',
              color: 'var(--ink3)',
            }}
          >
            Handbook
          </span>
          <div className="flex items-stretch min-w-0 flex-1 gap-0">
            {['ug', 'pg'].map((key) => {
              const file = key === 'ug' ? ugFile : pgFile
              const disabled = !file
              const on = file && selectedHandbookFile === file
              const label = key === 'ug' ? 'UG' : 'PG'
              return (
                <button
                  key={key}
                  type="button"
                  disabled={disabled}
                  onClick={() => file && setSelectedHandbookFile(file)}
                  className="font-mono shrink-0 px-2.5 h-9 -mb-px border-b-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{
                    fontSize: '10.5px',
                    letterSpacing: '0.04em',
                    color: on ? 'var(--accent)' : 'var(--ink3)',
                    borderBottomColor: on ? 'var(--accent)' : 'transparent',
                    background: 'none',
                    borderTop: 'none',
                    borderLeft: 'none',
                    borderRight: 'none',
                  }}
                  title={file ? file : `No ${label} handbook in the index`}
                >
                  {label}
                </button>
              )
            })}
          </div>
        </div>
      )}

      <div
        className="flex items-center gap-0 shrink-0 border-b px-6 h-10"
        style={{ borderColor: 'var(--rule)' }}
      >
        <span
          className="font-mono uppercase mr-3.5 shrink-0"
          style={{
            fontSize: 10,
            letterSpacing: '0.12em',
            color: 'var(--ink3)',
          }}
        >
          Retrieval
        </span>
        <div className="flex items-stretch min-w-0 flex-1 gap-0 overflow-x-auto">
          {METHODS.map((m) => {
            const on = method === m
            return (
              <button
                key={m}
                type="button"
                onClick={() => setMethod(m)}
                className="font-mono shrink-0 px-2.5 h-10 -mb-px border-b-2 transition-colors"
                style={{
                  fontSize: '10.5px',
                  letterSpacing: '0.04em',
                  color: on ? 'var(--accent)' : 'var(--ink3)',
                  borderBottomColor: on ? 'var(--accent)' : 'transparent',
                  background: 'none',
                  borderTop: 'none',
                  borderLeft: 'none',
                  borderRight: 'none',
                }}
              >
                {METHOD_LABELS[m]}
              </button>
            )
          })}
        </div>
        <div
          className="flex items-center gap-1.5 shrink-0 font-mono ml-2"
          style={{ fontSize: '10.5px', color: 'var(--ink3)' }}
        >
          <span>k =</span>
          <input
            type="number"
            min={1}
            max={20}
            value={k}
            onChange={(e) => setK(Math.min(20, Math.max(1, Number(e.target.value) || 1)))}
            className="w-8 text-center font-mono bg-transparent border-b outline-none p-0"
            style={{
              fontSize: '10.5px',
              color: 'var(--accent)',
              borderColor: 'var(--rule)',
            }}
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 px-7 py-8 messages-scroll">
        {messages.length === 0 && !isLoading ? (
          <EmptyState onSelect={(s) => onSend(s, method, k, generateAnswer)} />
        ) : (
          <div className="flex flex-col gap-7 w-full">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isLoading && <ChatMessage message={{ id: 'typing', role: 'typing' }} />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <ChatInput
        onSend={onSend}
        isLoading={isLoading}
        method={method}
        k={k}
        generateAnswer={generateAnswer}
        setGenerateAnswer={setGenerateAnswer}
      />
    </div>
  )
}
