import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/layout/Navbar'
import FileDropzone from '../components/ingest/FileDropzone'
import IngestProgress from '../components/ingest/IngestProgress'
import IndexStatusCard from '../components/ingest/IndexStatusCard'
import useAppStore from '../store/appStore'
import { ingestFiles, startIndexing } from '../api/ingest'
import { getStatus } from '../api/status'

/**
 * IngestPage — knowledge base management
 */
export default function IngestPage() {
  const {
    ingestProgress,
    setIngestProgress,
    resetIngestProgress,
    setIndexStatus,
  } = useAppStore()

  useEffect(() => {
    getStatus().then(setIndexStatus).catch(console.error)
  }, [setIndexStatus])

  const handleFilesSelected = async (files) => {
    resetIngestProgress()
    setIngestProgress({ status: 'ingesting', step: 'uploading', progress: 25 })

    try {
      await ingestFiles(files)
      setIngestProgress({ step: 'extracting', progress: 50 })
      await new Promise((r) => setTimeout(r, 1000))
      setIngestProgress({ step: 'chunking', progress: 75 })
      setIngestProgress({ step: 'indexing', progress: 90 })
      await startIndexing()
      setIngestProgress({ status: 'completed', step: 'indexing', progress: 100 })
      const status = await getStatus()
      setIndexStatus(status)
    } catch (error) {
      console.error('Ingestion failed:', error)
      setIngestProgress({
        status: 'error',
        error: error.response?.data?.detail || error.message,
      })
    }
  }

  return (
    <div className="h-full flex flex-col overflow-auto" style={{ background: '#2D3E50' }}>
      <Navbar />

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-10">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 mb-8" style={{ color: 'rgba(255,255,255,0.35)', fontSize: '0.8125rem' }}>
          <Link to="/" style={{ color: 'rgba(255,255,255,0.35)' }}>Chat</Link>
          <span>/</span>
          <span style={{ color: 'rgba(255,255,255,0.7)' }}>Knowledge Base</span>
        </div>

        <div className="mb-6">
          <h1 className="text-xl font-semibold text-white">Ingest Documents</h1>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Upload university handbooks to build the retrieval indexes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left — upload area */}
          <div className="md:col-span-2">
            <FileDropzone
              onFilesSelected={handleFilesSelected}
              disabled={ingestProgress.status === 'ingesting'}
            />
            <IngestProgress />
          </div>

          {/* Right — status */}
          <div className="flex flex-col gap-4">
            <IndexStatusCard />

            <div
              className="rounded-xl p-4 text-xs leading-relaxed"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: 'rgba(255,255,255,0.4)',
              }}
            >
              <p className="font-semibold mb-1.5" style={{ color: 'rgba(255,255,255,0.6)' }}>
                Processing notes
              </p>
              MinHash uses 128 permutations with 32 LSH bands. SimHash uses TF-IDF weighted fingerprints. Indexing completes in under 10 seconds for standard-size handbooks.
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
