import useAppStore from '../../store/appStore'

/**
 * IndexStatusCard — Summary of the current index state
 */
export default function IndexStatusCard() {
  const { indexStatus } = useAppStore()

  return (
    <div className="bg-navy-800 rounded-xl border border-navy-700 p-6 overflow-hidden relative">
      <div className="absolute top-0 right-0 w-32 h-32 bg-electric/5 rounded-full -mr-16 -mt-16 blur-3xl" />
      
      <h3 className="font-mono font-bold text-slate-400 text-xs uppercase tracking-widest mb-4">Storage Metadata</h3>
      
      <div className="grid grid-cols-2 gap-6">
        <div>
          <p className="text-slate-500 text-xs font-mono uppercase">Status</p>
          <p className={`text-lg font-bold mt-1 ${indexStatus.is_indexed ? 'text-green-400' : 'text-red-400'}`}>
            {indexStatus.is_indexed ? 'ONLINE' : 'OFFLINE'}
          </p>
        </div>
        <div>
          <p className="text-slate-500 text-xs font-mono uppercase">Total Chunks</p>
          <p className="text-xl font-mono font-bold mt-1 text-white">{indexStatus.num_chunks}</p>
        </div>
        <div className="col-span-2">
          <p className="text-slate-500 text-xs font-mono uppercase">Last Index Update</p>
          <p className="text-sm font-mono mt-1 text-slate-300">
            {indexStatus.last_updated ? new Date(indexStatus.last_updated).toLocaleString() : 'N/A'}
          </p>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-navy-700 flex flex-wrap gap-2">
        <span className="px-2 py-1 bg-navy-700 rounded text-[10px] font-mono text-slate-400 border border-navy-600">MINHASH (LSH)</span>
        <span className="px-2 py-1 bg-navy-700 rounded text-[10px] font-mono text-slate-400 border border-navy-600">SIMHASH</span>
        <span className="px-2 py-1 bg-navy-700 rounded text-[10px] font-mono text-slate-400 border border-navy-600">TF-IDF</span>
      </div>
    </div>
  )
}
