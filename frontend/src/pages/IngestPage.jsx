import { useEffect } from 'react'
import PageWrapper from '../components/layout/PageWrapper'
import FileDropzone from '../components/ingest/FileDropzone'
import IngestProgress from '../components/ingest/IngestProgress'
import IndexStatusCard from '../components/ingest/IndexStatusCard'
import useAppStore from '../store/appStore'
import { ingestFiles, startIndexing } from '../api/ingest'
import { getStatus } from '../api/status'

export default function IngestPage() {
  const { 
    ingestProgress, 
    setIngestProgress, 
    resetIngestProgress,
    setIndexStatus 
  } = useAppStore()

  useEffect(() => {
    // Initial status check
    getStatus().then(setIndexStatus).catch(console.error)
  }, [setIndexStatus])

  const handleFilesSelected = async (files) => {
    resetIngestProgress()
    setIngestProgress({ status: 'ingesting', step: 'uploading', progress: 25 })
    
    try {
      // 1. Upload
      await ingestFiles(files)
      setIngestProgress({ step: 'extracting', progress: 50 })
      
      // Simulate extraction time for better UX
      await new Promise(r => setTimeout(r, 1000))
      setIngestProgress({ step: 'chunking', progress: 75 })
      
      // 2. Index
      setIngestProgress({ step: 'indexing', progress: 90 })
      await startIndexing()
      
      setIngestProgress({ status: 'completed', step: 'indexing', progress: 100 })
      
      // Refresh status
      const status = await getStatus()
      setIndexStatus(status)
    } catch (error) {
      console.error('Ingestion failed:', error)
      setIngestProgress({ 
        status: 'error', 
        error: error.response?.data?.detail || error.message 
      })
    }
  }

  return (
    <PageWrapper>
      <div className="max-w-4xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-bold">Ingest Knowledge Base</h1>
          <p className="text-slate-400 mt-2">Upload university handbooks to build the search indexes.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-8">
            <FileDropzone 
              onFilesSelected={handleFilesSelected} 
              disabled={ingestProgress.status === 'ingesting'} 
            />
            <IngestProgress />
          </div>
          
          <div>
            <IndexStatusCard />
            
            <div className="mt-6 p-4 rounded-xl bg-amber/10 border border-amber/20 text-amber/80 text-sm">
              <p className="font-bold flex items-center gap-2 mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Processing Note
              </p>
              Extraction and indexing uses MinHash (128 permutations) and LSH (32 bands) for sub-second similarity matching.
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}
