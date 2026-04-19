import ChunkCard from './ChunkCard'
import LatencyBadge from '../ui/LatencyBadge'

/**
 * MethodColumn — A single column in the three-column view
 * @param {Object} props
 * @param {string} props.name - Method name
 * @param {Object} props.data - Result data for this method
 * @param {Array} props.sharedIds - List of chunk IDs that appear in multiple columns
 */
export default function MethodColumn({ name, data, sharedIds }) {
  if (!data) return null

  return (
    <div className="flex flex-col h-full min-w-[320px] bg-navy-900/30 rounded-2xl border border-navy-800 overflow-hidden">
      <div className="p-4 border-b border-navy-800 bg-navy-800/20 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-mono font-bold uppercase tracking-widest text-white">{name}</h3>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5">TOP-{data.chunks.length} RETRIEVAL</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <LatencyBadge ms={data.latency_ms} />
          {data.memory_mb !== undefined && (
            <div className="text-[9px] font-mono text-slate-500 uppercase">
              {data.memory_mb.toFixed(1)} MB RAM
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {data.chunks.length > 0 ? (
          data.chunks.map((chunk, idx) => (
            <ChunkCard 
              key={`${name}-${idx}`} 
              chunk={chunk} 
              isShared={sharedIds.includes(chunk.chunk_id)}
            />
          ))
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center p-8">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-2 opacity-20"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <p className="text-xs font-mono uppercase tracking-tighter">No relevant chunks found</p>
          </div>
        )}
      </div>
    </div>
  )
}
