import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * Renders assistant message body as GitHub-flavored Markdown (lists, **bold**, rules, etc.).
 * @param {Object} props
 * @param {string} props.children - Raw markdown string from the API
 */
export default function ChatMarkdown({ children }) {
  const text = typeof children === 'string' ? children : ''
  if (!text.trim()) {
    return null
  }

  return (
    <div className="chat-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children: linkChildren, ...rest }) => (
            <a
              href={href}
              {...rest}
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 decoration-[var(--accent)]/50 hover:decoration-[var(--accent)]"
              style={{ color: 'var(--accent)' }}
            >
              {linkChildren}
            </a>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}
