/**
 * MethodTabs — tab switcher shown when method=ALL in evidence panel
 * @param {Object} props
 * @param {string} props.active - currently active method key
 * @param {Function} props.onChange - (key) => void
 * @param {Object} props.latencies - { hybrid, minhash, simhash, tfidf } latency_ms values
 * @param {number} props.overlapCount - chunks that appear in all methods
 */
export default function MethodTabs({ active, onChange, latencies = {}, overlapCount = 0 }) {
  const tabs = [
    { key: 'hybrid',  label: 'Hybrid'  },
    { key: 'minhash', label: 'MinHash' },
    { key: 'simhash', label: 'SimHash' },
    { key: 'tfidf',   label: 'TF-IDF'  },
  ]

  return (
    <div className="flex items-center gap-1">
      {tabs.map(({ key, label }) => {
        const ms = latencies[key]
        const isActive = active === key
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={{
              background: isActive ? 'rgba(255,255,255,0.12)' : 'transparent',
              color: isActive ? '#fff' : 'rgba(255,255,255,0.4)',
              border: isActive ? '1px solid rgba(255,255,255,0.18)' : '1px solid transparent',
            }}
          >
            {label}
            {ms !== undefined && (
              <span
                className="text-[9px] font-semibold px-1 py-0.5 rounded"
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  color: 'rgba(255,255,255,0.4)',
                }}
              >
                {ms < 1 ? '<1' : Math.round(ms)}ms
              </span>
            )}
          </button>
        )
      })}

      {overlapCount > 0 && (
        <div
          className="ml-auto flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-lg"
          style={{ background: 'rgba(52,211,153,0.1)', color: '#6ee7b7' }}
        >
          <span>✓</span>
          <span>{overlapCount} shared</span>
        </div>
      )}
    </div>
  )
}
