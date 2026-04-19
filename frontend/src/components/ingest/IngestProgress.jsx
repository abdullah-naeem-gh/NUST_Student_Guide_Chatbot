import useAppStore from '../../store/appStore'

/**
 * IngestProgress — Displays step-by-step progress of ingestion
 */
export default function IngestProgress() {
  const { ingestProgress } = useAppStore()
  
  if (ingestProgress.status === 'idle') return null

  const steps = [
    { id: 'uploading', label: 'Uploading Files' },
    { id: 'extracting', label: 'Extracting Text' },
    { id: 'chunking', label: 'Creating Chunks' },
    { id: 'indexing', label: 'Building LSH & SimHash' },
  ]

  const currentStepIndex = steps.findIndex(s => s.id === ingestProgress.step)

  return (
    <div className="mt-8 bg-navy-800/50 rounded-xl border border-navy-700 p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-mono font-bold uppercase tracking-widest text-sm text-slate-400">Ingestion Pipeline</h3>
        <span className={`text-xs px-2 py-1 rounded font-mono ${
          ingestProgress.status === 'error' ? 'bg-red-500/20 text-red-400' :
          ingestProgress.status === 'completed' ? 'bg-green-500/20 text-green-400' :
          'bg-electric/20 text-electric'
        }`}>
          {ingestProgress.status.toUpperCase()}
        </span>
      </div>

      <div className="space-y-4">
        {steps.map((step, index) => {
          const isDone = index < currentStepIndex || ingestProgress.status === 'completed'
          const isActive = index === currentStepIndex && ingestProgress.status === 'ingesting'
          
          return (
            <div key={step.id} className="flex items-center gap-4">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono border ${
                isDone ? 'bg-green-500 border-green-500 text-navy-900' :
                isActive ? 'border-electric text-electric animate-pulse' :
                'border-navy-600 text-slate-500'
              }`}>
                {isDone ? '✓' : index + 1}
              </div>
              <span className={`text-sm ${isDone ? 'text-slate-200' : isActive ? 'text-white font-medium' : 'text-slate-500'}`}>
                {step.label}
              </span>
              {isActive && (
                <div className="flex-1 h-1 bg-navy-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-electric transition-all duration-500" 
                    style={{ width: `${ingestProgress.progress}%` }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {ingestProgress.error && (
        <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm font-mono">
          ERROR: {ingestProgress.error}
        </div>
      )}
    </div>
  )
}
