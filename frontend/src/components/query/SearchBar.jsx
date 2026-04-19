import { useState } from 'react'

/**
 * SearchBar — Input with method toggle and k-selector
 * @param {Object} props
 * @param {Function} props.onSearch - Callback for search
 * @param {boolean} props.isLoading - Whether searching is active
 */
export default function SearchBar({ onSearch, isLoading }) {
  const [query, setQuery] = useState('')
  const [method, setMethod] = useState('all')
  const [k, setK] = useState(5)
  const [generateAnswer, setGenerateAnswer] = useState(true)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query, method, k, generateAnswer)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-4">
      <div className="relative group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about academic policies, rules, or guidelines..."
          className="w-full bg-navy-800 border border-navy-700 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-electric/50 focus:border-electric transition-all text-lg shadow-xl"
          disabled={isLoading}
        />
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-electric transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </div>
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 px-6 py-2 bg-electric text-white rounded-lg font-bold hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : 'SEARCH'}
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 px-2">
        <div className="flex flex-wrap items-center gap-6">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-slate-500">Method:</span>
            <div className="flex bg-navy-800 p-1 rounded-lg border border-navy-700">
              {['all', 'minhash', 'simhash', 'tfidf'].map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMethod(m)}
                  className={`px-3 py-1 rounded text-xs font-mono uppercase transition-all ${
                    method === m ? 'bg-electric text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-slate-500">Top-K:</span>
            <select
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              className="bg-navy-800 border border-navy-700 rounded-lg px-3 py-1 text-xs font-mono text-white focus:outline-none focus:border-electric transition-colors"
            >
              {[3, 5, 10, 20].map(val => (
                <option key={val} value={val}>{val}</option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 cursor-pointer group">
            <div className={`w-10 h-5 rounded-full p-1 transition-colors ${generateAnswer ? 'bg-electric' : 'bg-navy-700'}`}>
              <div className={`w-3 h-3 bg-white rounded-full transition-transform ${generateAnswer ? 'translate-x-5' : 'translate-x-0'}`} />
            </div>
            <input 
              type="checkbox" 
              className="hidden" 
              checked={generateAnswer}
              onChange={() => setGenerateAnswer(!generateAnswer)}
            />
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-slate-500 group-hover:text-slate-300 transition-colors">
              AI Answer
            </span>
          </label>
        </div>
      </div>
    </form>
  )
}
