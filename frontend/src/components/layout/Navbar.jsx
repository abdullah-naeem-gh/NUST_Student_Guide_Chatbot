import { Link, useLocation } from 'react-router-dom'
import useAppStore from '../../store/appStore'

/**
 * Navbar component for navigation and global status
 */
export default function Navbar() {
  const { indexStatus, darkMode, toggleDarkMode } = useAppStore()
  const location = useLocation()

  return (
    <nav className="h-16 border-b border-navy-700 bg-navy-900/50 backdrop-blur-md sticky top-0 z-50 px-6 flex items-center justify-between">
      <div className="flex items-center gap-8">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-electric rounded flex items-center justify-center font-mono font-bold text-white">
            N
          </div>
          <span className="font-mono font-bold text-xl tracking-tight hidden sm:inline">
            NUST <span className="text-electric">GUIDE</span>
          </span>
        </Link>

        <div className="flex items-center gap-1">
          <NavLink to="/" active={location.pathname === '/'}>Query</NavLink>
          <NavLink to="/ingest" active={location.pathname === '/ingest'}>Ingest</NavLink>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Index Status Dot */}
        <div className="flex items-center gap-2 px-3 py-1 bg-navy-800 rounded-full border border-navy-700">
          <div className={`w-2 h-2 rounded-full ${indexStatus.is_indexed ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`} />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            {indexStatus.is_indexed ? `${indexStatus.num_chunks} Chunks` : 'No Index'}
          </span>
        </div>

        {/* Dark Mode Toggle */}
        <button 
          onClick={toggleDarkMode}
          className="p-2 hover:bg-navy-800 rounded-lg transition-colors text-slate-400 hover:text-white"
          title="Toggle Dark Mode"
        >
          {darkMode ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          )}
        </button>
      </div>
    </nav>
  )
}

function NavLink({ to, children, active }) {
  return (
    <Link 
      to={to} 
      className={`px-4 py-2 rounded-lg font-medium text-sm transition-all ${
        active 
          ? 'text-white bg-electric/10' 
          : 'text-slate-400 hover:text-white hover:bg-navy-800'
      }`}
    >
      {children}
    </Link>
  )
}
