/**
 * LatencyBadge — Shows execution time with color coding
 * @param {Object} props
 * @param {number} props.ms - Latency in milliseconds
 */
export default function LatencyBadge({ ms }) {
  let colorClass = 'text-green-400 bg-green-400/10 border-green-400/20'
  if (ms > 300) colorClass = 'text-amber bg-amber/10 border-amber/20'
  if (ms > 1000) colorClass = 'text-red-400 bg-red-400/10 border-red-400/20'

  return (
    <div className={`px-2 py-0.5 rounded border text-[10px] font-mono font-bold flex items-center gap-1 ${colorClass}`}>
      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      {ms.toFixed(0)}ms
    </div>
  )
}
