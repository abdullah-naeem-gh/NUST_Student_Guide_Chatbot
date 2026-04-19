import useAppStore from '../../store/appStore'

const STEPS = [
  { id: 'uploading',  label: 'Uploading files'         },
  { id: 'extracting', label: 'Extracting text'          },
  { id: 'chunking',   label: 'Creating chunks'          },
  { id: 'indexing',   label: 'Building LSH & SimHash'   },
]

/**
 * IngestProgress — step indicator for the ingestion pipeline
 */
export default function IngestProgress() {
  const { ingestProgress } = useAppStore()

  if (ingestProgress.status === 'idle') return null

  const currentIdx = STEPS.findIndex((s) => s.id === ingestProgress.step)
  const isError = ingestProgress.status === 'error'
  const isDone = ingestProgress.status === 'completed'

  return (
    <div
      className="rounded-xl p-5 mt-6"
      style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <div className="flex items-center justify-between mb-5">
        <span className="text-xs font-semibold text-white" style={{ letterSpacing: '0.05em' }}>
          Pipeline
        </span>
        <span
          className="text-[10px] font-semibold px-2 py-0.5 rounded"
          style={{
            background: isError ? 'rgba(248,113,113,0.15)' : isDone ? 'rgba(52,211,153,0.15)' : 'rgba(255,255,255,0.08)',
            color: isError ? '#f87171' : isDone ? '#6ee7b7' : 'rgba(255,255,255,0.5)',
          }}
        >
          {ingestProgress.status.toUpperCase()}
        </span>
      </div>

      <div className="flex flex-col gap-3">
        {STEPS.map((step, idx) => {
          const done = idx < currentIdx || isDone
          const active = idx === currentIdx && ingestProgress.status === 'ingesting'

          return (
            <div key={step.id} className="flex items-center gap-3">
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
                style={{
                  background: done ? 'rgba(52,211,153,0.2)' : active ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.05)',
                  border: done ? '1px solid rgba(52,211,153,0.4)' : active ? '1px solid rgba(255,255,255,0.25)' : '1px solid rgba(255,255,255,0.08)',
                  color: done ? '#6ee7b7' : active ? '#fff' : 'rgba(255,255,255,0.2)',
                }}
              >
                {done ? '✓' : idx + 1}
              </div>

              <span
                className="text-sm flex-1"
                style={{
                  color: done ? 'rgba(255,255,255,0.8)' : active ? '#fff' : 'rgba(255,255,255,0.3)',
                  fontWeight: active ? 500 : 400,
                }}
              >
                {step.label}
              </span>

              {active && (
                <div
                  className="h-1 w-24 rounded-full overflow-hidden"
                  style={{ background: 'rgba(255,255,255,0.08)' }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${ingestProgress.progress}%`,
                      background: 'rgba(255,255,255,0.35)',
                    }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {ingestProgress.error && (
        <div
          className="mt-4 rounded-lg p-3 text-xs"
          style={{
            background: 'rgba(248,113,113,0.1)',
            border: '1px solid rgba(248,113,113,0.2)',
            color: '#fca5a5',
          }}
        >
          {ingestProgress.error}
        </div>
      )}
    </div>
  )
}
