import { useState, useRef, useEffect } from 'react'

/**
 * Bottom input: optional AI toggle + underline field + Send.
 * @param {Object} props
 * @param {Function} props.onSend - (query, method, k, generateAnswer) => void
 * @param {boolean} props.isLoading
 * @param {string} props.method
 * @param {number} props.k
 * @param {boolean} props.generateAnswer
 * @param {Function} props.setGenerateAnswer
 */
export default function ChatInput({
  onSend,
  isLoading,
  method,
  k,
  generateAnswer,
  setGenerateAnswer,
}) {
  const [query, setQuery] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [query])

  const handleSubmit = () => {
    if (!query.trim() || isLoading) return
    onSend(query.trim(), method, k, generateAnswer)
    setQuery('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div
      className="shrink-0 border-t px-7 py-4"
      style={{ borderColor: 'var(--rule)', background: 'var(--paper)' }}
    >
      <label className="flex items-center gap-2 cursor-pointer mb-3 font-mono text-[10px] uppercase tracking-wide" style={{ color: 'var(--ink3)' }}>
        <input
          type="checkbox"
          checked={generateAnswer}
          onChange={(e) => setGenerateAnswer(e.target.checked)}
          className="rounded border"
          style={{ accentColor: 'var(--accent)' }}
        />
        Generate AI answer
      </label>

      <div className="flex items-end gap-3">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about academic policies…"
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-transparent outline-none resize-none py-1.5 min-h-[36px] max-h-[120px] text-[13.5px] leading-relaxed border-b transition-colors placeholder:italic placeholder:text-[var(--ink3)]"
          style={{
            fontFamily: 'Lora, Georgia, serif',
            color: 'var(--ink)',
            borderColor: 'var(--rule)',
            caretColor: 'var(--accent)',
          }}
          onFocus={(e) => {
            e.target.style.borderColor = 'var(--accent)'
          }}
          onBlur={(e) => {
            e.target.style.borderColor = 'var(--rule)'
          }}
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isLoading || !query.trim()}
          className="font-mono uppercase shrink-0 px-3.5 py-1.5 transition-colors text-[10px] tracking-[0.1em]"
          style={{
            border: '1px solid var(--accent)',
            borderRadius: 1,
            background: 'transparent',
            color: query.trim() && !isLoading ? 'var(--accent)' : 'var(--ink3)',
            opacity: query.trim() && !isLoading ? 1 : 0.62,
          }}
        >
          {isLoading ? '…' : 'Send'}
        </button>
      </div>
    </div>
  )
}
