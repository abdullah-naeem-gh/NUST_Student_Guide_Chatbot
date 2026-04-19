import client from './client'

/**
 * runQuery - execute a search query against the backend
 * @param {string} query - The search query string
 * @param {string} method - 'minhash', 'simhash', 'tfidf', or 'all'
 * @param {number} k - Number of results to retrieve (top-k)
 * @param {boolean} generateAnswer - Whether to generate an LLM answer
 * @param {string|null} [sourceFile] - Limit retrieval to this PDF (e.g. UG_Handbook.pdf)
 */
export async function runQuery(
  query,
  method = 'all',
  k = 5,
  generateAnswer = true,
  sourceFile = null
) {
  const body = {
    query,
    method,
    k,
    generate_answer: generateAnswer,
  }
  if (sourceFile) {
    body.source_file = sourceFile
  }
  // Trailing slash matches FastAPI route `/query/` and avoids 307 redirects (CORS/extra round-trips).
  const { data } = await client.post('/query/', body, { timeout: 120_000 })
  return data
}
