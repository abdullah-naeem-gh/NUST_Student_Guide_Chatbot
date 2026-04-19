import { Link } from 'react-router-dom'
import useAppStore from '../../store/appStore'

/**
 * Top bar: wordmark, index status, optional library label from indexed PDF name.
 */
export default function Navbar() {
  const { indexStatus, darkMode, toggleDarkMode, selectedHandbookFile } = useAppStore()

  const libLabel =
    fileBasename(selectedHandbookFile || indexStatus.source_file) || 'Knowledge base'

  return (
    <header
      className="h-[52px] shrink-0 flex items-center px-8 border-b gap-4"
      style={{
        background: 'var(--paper)',
        borderColor: 'var(--rule)',
      }}
    >
      <Link to="/" className="select-none shrink-0">
        <div
          className="font-mono text-[12.5px] tracking-[0.18em] uppercase"
          style={{ color: 'var(--ink)', fontWeight: 400 }}
        >
          NUST <span style={{ color: 'var(--ink3)' }}>/ Guide</span>
        </div>
      </Link>

      <div
        className="ml-auto flex items-center gap-6 font-mono text-[11px] shrink-0 min-w-0"
        style={{ color: 'var(--ink3)' }}
      >
        <span className="hidden sm:inline-flex items-center gap-1.5 truncate" title={libLabel}>
          <span
            className="inline-block w-[5px] h-[5px] rounded-full shrink-0"
            style={{ background: 'var(--accent)' }}
          />
          {indexStatus.is_indexed ? (
            <>
              indexed · {indexStatus.num_chunks.toLocaleString()} chunks
            </>
          ) : (
            'not indexed'
          )}
        </span>
        <span className="hidden md:inline truncate max-w-[220px] lg:max-w-[320px]">{libLabel}</span>

        <Link
          to="/ingest"
          className="p-1.5 rounded transition-colors shrink-0"
          style={{ color: 'var(--ink3)' }}
          title="Manage knowledge base"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </Link>

        <button
          type="button"
          onClick={toggleDarkMode}
          className="p-1.5 rounded transition-colors shrink-0"
          style={{ color: 'var(--ink3)' }}
          title="Toggle alternate theme"
        >
          {darkMode ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </button>
      </div>
    </header>
  )
}

function fileBasename(path) {
  if (!path || typeof path !== 'string') return ''
  const parts = path.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] || ''
}
