const SUGGESTIONS = [
  'What is the minimum GPA requirement?',
  'What is the attendance policy?',
  'How many times can a course be repeated?',
  'What happens if a student fails a course?',
  "What are the requirements for Dean's List?",
]

/**
 * @param {Object} props
 * @param {Function} props.onSelect
 */
export default function EmptyState({ onSelect }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[240px] px-2 pb-6 gap-8">
      <div className="text-center">
        <p className="font-semibold text-base" style={{ color: 'var(--ink)' }}>
          NUST Guide
        </p>
        <p className="text-[0.8125rem] mt-1" style={{ color: 'var(--ink3)' }}>
          Ask anything about academic policies
        </p>
      </div>

      <div className="flex flex-col gap-2 w-full">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSelect(s)}
            className="text-left px-4 py-3 rounded-sm text-sm transition-colors border"
            style={{
              background: 'var(--bg)',
              borderColor: 'var(--rule)',
              color: 'var(--ink2)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent)'
              e.currentTarget.style.color = 'var(--ink)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--rule)'
              e.currentTarget.style.color = 'var(--ink2)'
            }}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
