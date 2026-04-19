import useAppStore from '../../store/appStore'

/**
 * IndexStatusCard — index metadata summary
 */
export default function IndexStatusCard() {
  const { indexStatus } = useAppStore()

  return (
    <div
      className="rounded-xl p-5"
      style={{
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <p className="text-xs font-semibold text-white mb-4" style={{ letterSpacing: '0.05em' }}>
        Index Status
      </p>

      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>Status</span>
          <div className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{ background: indexStatus.is_indexed ? '#34d399' : '#f87171' }}
            />
            <span
              className="text-xs font-semibold"
              style={{ color: indexStatus.is_indexed ? '#6ee7b7' : '#fca5a5' }}
            >
              {indexStatus.is_indexed ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>Chunks</span>
          <span className="text-xs font-semibold text-white">{indexStatus.num_chunks}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>Updated</span>
          <span className="text-xs" style={{ color: 'rgba(255,255,255,0.6)' }}>
            {indexStatus.last_updated
              ? new Date(indexStatus.last_updated).toLocaleDateString()
              : '—'}
          </span>
        </div>
      </div>

      <div
        className="mt-4 pt-4 flex flex-wrap gap-1.5"
        style={{ borderTop: '1px solid rgba(255,255,255,0.08)' }}
      >
        {['MinHash LSH', 'SimHash', 'TF-IDF'].map((label) => (
          <span
            key={label}
            className="text-[10px] font-medium px-2 py-0.5 rounded"
            style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(255,255,255,0.4)',
            }}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  )
}
