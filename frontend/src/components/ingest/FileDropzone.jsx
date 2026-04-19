import { useState, useCallback } from 'react'

/**
 * FileDropzone — Component to handle PDF uploads
 * @param {Object} props
 * @param {Function} props.onFilesSelected - Callback when files are dropped or selected
 * @param {boolean} props.disabled - Whether the component is disabled
 */
export default function FileDropzone({ onFilesSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    if (!disabled) setIsDragging(true)
  }, [disabled])

  const handleDragLeave = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return

    const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf')
    if (files.length > 0) {
      onFilesSelected(files)
    }
  }, [onFilesSelected, disabled])

  const handleFileInput = useCallback((e) => {
    const files = Array.from(e.target.files).filter(f => f.type === 'application/pdf')
    if (files.length > 0) {
      onFilesSelected(files)
    }
  }, [onFilesSelected])

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`relative h-64 border-2 border-dashed rounded-xl transition-all flex flex-col items-center justify-center gap-4 ${
        disabled ? 'opacity-50 cursor-not-allowed border-navy-700 bg-navy-800/50' :
        isDragging ? 'border-electric bg-electric/10 scale-[1.01]' : 'border-navy-700 bg-navy-800/30 hover:bg-navy-800/50 hover:border-navy-600'
      }`}
    >
      <input
        type="file"
        multiple
        accept=".pdf"
        onChange={handleFileInput}
        className="absolute inset-0 opacity-0 cursor-pointer"
        disabled={disabled}
      />
      
      <div className="w-16 h-16 bg-navy-700 rounded-full flex items-center justify-center text-electric">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      </div>
      
      <div className="text-center">
        <p className="text-lg font-medium">Drop academic handbooks here</p>
        <p className="text-sm text-slate-400 mt-1">Only PDF files are supported</p>
      </div>

      <div className="px-4 py-2 bg-electric text-white rounded-lg text-sm font-bold uppercase tracking-wider">
        Select Files
      </div>
    </div>
  )
}
