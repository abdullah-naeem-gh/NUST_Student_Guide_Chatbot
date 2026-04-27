import { Link } from 'react-router-dom'
import useAppStore from '../../store/appStore'
import { parseSourceFilesFromStatus, resolveHandbookFiles } from '../../lib/handbooks'

export default function Navbar({ screen, onNavigate }) {
  const { indexStatus, selectedHandbookFile, setSelectedHandbookFile } = useAppStore()

  const files = parseSourceFilesFromStatus(indexStatus)
  const { ug: ugFile, pg: pgFile } = resolveHandbookFiles(files)
  const showPicker = screen === 'chat' && (ugFile || pgFile)
  const logoContent = (
    <>
      <div style={{
        width: 28, height: 28, background: 'var(--accent)', borderRadius: 6,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
      </div>
      <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: '-0.01em', color: 'var(--ink)' }}>NUST</span>
      <span style={{ color: 'var(--rule)', fontWeight: 400 }}>/</span>
      <span style={{ fontWeight: 500, fontSize: 14, color: 'var(--ink2)' }}>Guide</span>
    </>
  )

  return (
    <header style={{
      height: 'var(--nav-h)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      background: 'var(--paper)',
      borderBottom: '1px solid var(--rule)',
      flexShrink: 0,
      gap: 16,
      position: 'relative',
      zIndex: 10,
      fontFamily: 'var(--font-sans)',
    }}>
      {/* Logo */}
      {onNavigate ? (
        <button
          onClick={() => onNavigate('landing')}
          style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
        >
          {logoContent}
        </button>
      ) : (
        <Link
          to="/"
          style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}
        >
          {logoContent}
        </Link>
      )}

      {/* UG / PG switcher — only on chat screen */}
      {showPicker && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 8 }}>
          {[['ug', ugFile], ['pg', pgFile]].map(([key, file]) => {
            const on = file && selectedHandbookFile === file
            return (
              <button
                key={key}
                type="button"
                disabled={!file}
                onClick={() => file && setSelectedHandbookFile(file)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  background: on ? 'var(--accent)' : 'transparent',
                  color: on ? 'white' : 'var(--ink3)',
                  border: on ? '1px solid var(--accent)' : '1px solid var(--rule)',
                  transition: 'all 0.15s',
                  cursor: file ? 'pointer' : 'not-allowed',
                  opacity: file ? 1 : 0.4,
                  fontFamily: 'var(--font-sans)',
                }}
                title={file ?? `No ${key.toUpperCase()} handbook indexed`}
              >
                {key}
              </button>
            )
          })}
        </div>
      )}

      {/* Right side */}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Index status dot */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: indexStatus.is_indexed ? '#22c55e' : 'var(--ink3)',
            flexShrink: 0,
          }} />
          <span style={{ fontSize: 12, color: 'var(--ink3)', fontWeight: 500, fontFamily: 'var(--font-sans)' }}>
            {indexStatus.is_indexed
              ? `${indexStatus.num_chunks.toLocaleString()} chunks indexed`
              : 'Not indexed'}
          </span>
        </div>

        <Link
          to="/analytics"
          style={{
            padding: '6px 14px',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 600,
            background: 'transparent',
            color: 'var(--ink3)',
            border: '1px solid var(--rule)',
            transition: 'all 0.15s',
            textDecoration: 'none',
            fontFamily: 'var(--font-sans)',
          }}
        >
          Analytics
        </Link>

        {/* Open Chat button */}
        <Link
          to="/chat"
          onClick={onNavigate ? () => onNavigate('chat') : undefined}
          style={{
            padding: '6px 14px',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 600,
            background: 'transparent',
            color: 'var(--ink3)',
            border: '1px solid var(--rule)',
            transition: 'all 0.15s',
            textDecoration: 'none',
            fontFamily: 'var(--font-sans)',
            cursor: 'pointer',
          }}
        >
          Open Chat →
        </Link>
      </div>
    </header>
  )
}
