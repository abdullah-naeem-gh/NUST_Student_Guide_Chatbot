import { useState, useEffect, useMemo } from 'react'
import PageWrapper from '../components/layout/PageWrapper'
import SearchBar from '../components/query/SearchBar'
import AnswerCard from '../components/query/AnswerCard'
import MethodColumn from '../components/query/MethodColumn'
import ChunkCard from '../components/query/ChunkCard'
import LatencyBadge from '../components/ui/LatencyBadge'
import useAppStore from '../store/appStore'
import { runQuery } from '../api/query'
import { getStatus } from '../api/status'

export default function QueryPage() {
  const { 
    queryResults, 
    setQueryResults, 
    isLoading, 
    setLoading, 
    setIndexStatus 
  } = useAppStore()

  const [currentMethod, setCurrentMethod] = useState('all')

  useEffect(() => {
    getStatus().then(setIndexStatus).catch(console.error)
  }, [setIndexStatus])

  const handleSearch = async (query, method, k, generateAnswer) => {
    setLoading(true)
    setCurrentMethod(method)
    try {
      const results = await runQuery(query, method, k, generateAnswer)
      setQueryResults(results)
    } catch (error) {
      console.error('Search failed:', error)
      // Toast error would be nice here
    } finally {
      setLoading(false)
    }
  }

  // Find chunks that appear in more than one method
  const sharedIds = useMemo(() => {
    if (!queryResults || currentMethod !== 'all') return []
    
    const idCounts = {}
    const methods = ['minhash', 'simhash', 'tfidf']
    
    methods.forEach(m => {
      if (queryResults.results && queryResults.results[m]) {
        queryResults.results[m].chunks.forEach(chunk => {
          idCounts[chunk.chunk_id] = (idCounts[chunk.chunk_id] || 0) + 1
        })
      }
    })
    
    return Object.keys(idCounts).filter(id => idCounts[id] > 1)
  }, [queryResults, currentMethod])

  return (
    <PageWrapper>
      <div className="space-y-8">
        <section className="max-w-4xl mx-auto w-full">
          <header className="mb-8 text-center">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              Academic Policy QA
            </h1>
            <p className="text-slate-400 mt-2">
              Cross-method retrieval comparison for university handbooks.
            </p>
          </header>
          
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        </section>

        {queryResults && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Answer Section */}
          {queryResults.answer && (
            <div className="max-w-4xl mx-auto">
              <AnswerCard 
                answer={queryResults.answer} 
                citations={queryResults.cited_chunks} 
              />
            </div>
          )}

            {/* Results Grid / Columns */}
            {currentMethod === 'all' ? (
              <div className="flex flex-col lg:flex-row gap-6 h-[700px]">
          <MethodColumn 
            name="MinHash + LSH" 
            data={queryResults.results.minhash} 
            sharedIds={sharedIds}
          />
          <MethodColumn 
            name="SimHash" 
            data={queryResults.results.simhash} 
            sharedIds={sharedIds}
          />
          <MethodColumn 
            name="TF-IDF" 
            data={queryResults.results.tfidf} 
            sharedIds={sharedIds}
          />
        </div>
      ) : (
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-4 px-2">
            <h3 className="font-mono font-bold uppercase tracking-widest text-sm text-slate-400">
              {currentMethod} Results
            </h3>
            {queryResults.results[currentMethod] && (
              <LatencyBadge ms={queryResults.results[currentMethod].latency_ms} />
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {queryResults.results[currentMethod]?.chunks.map((chunk, idx) => (
              <ChunkCard key={idx} chunk={chunk} isShared={false} />
            ))}
          </div>
        </div>
      )}
          </div>
        )}

        {!queryResults && !isLoading && (
          <div className="max-w-4xl mx-auto text-center py-20 border-2 border-dashed border-navy-800 rounded-3xl">
            <div className="w-16 h-16 bg-navy-800 text-slate-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </div>
            <h3 className="text-slate-400 font-medium">Ready for your query</h3>
            <p className="text-slate-500 text-sm mt-1">Enter a question above to begin retrieval analysis.</p>
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
