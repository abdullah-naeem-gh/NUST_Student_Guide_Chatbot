import { useState, useCallback } from 'react'

/**
 * FileDropzone — handles PDF uploads with drag-and-drop
 * @param {Object} props
 * @param {Function} props.onFilesSelected - called with File[]
 * @param {boolean} props.disabled
 */
export default function FileDropzone({ onFilesSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    if (!disabled) setIsDragging(true)
  }, [disabled])

  const handleDragLeave = useCallback(() => setIsDragging(false), [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const files = Array.from(e.dataTransfer.files).filter((f) => f.type === 'application/pdf')
    if (files.length) onFilesSelected(files)
  }, [onFilesSelected, disabled])

  const handleFileInput = useCallback((e) => {
    const files = Array.from(e.target.files).filter((f) => f.type === 'application/pdf')
    if (files.length) onFilesSelected(files)
  }, [onFilesSelected])

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="relative h-52 rounded-xl flex flex-col items-center justify-center gap-4 transition-all"
      style={{
        border: isDragging
          ? '1.5px dashed rgba(255,255,255,0.35)'
          : '1.5px dashed rgba(255,255,255,0.12)',
        background: isDragging
          ? 'rgba(255,255,255,0.06)'
          : 'rgba(255,255,255,0.03)',
        opacity: disabled ? 0.5 : 1,
        cursor: disabled ? 'not-allowed' : 'default',
      }}
    >
      <input
        type="file"
        multiple
        accept=".pdf"
        onChange={handleFileInput}
        className="absolute inset-0 opacity-0 cursor-pointer"
        disabled={disabled}
      />

      <div
        className="w-12 h-12 rounded-xl flex items-center justify-center"
        style={{ background: 'rgba(255,255,255,0.08)' }}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'rgba(255,255,255,0.5)' }}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>

      <div className="text-center">
        <p className="text-sm font-medium text-white">Drop PDF handbooks here</p>
        <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.35)' }}>
          or click to browse
        </p>
      </div>
    </div>
  )
}
