import client from './client'

/**
 * runQuery - execute a search query against the backend
 * @param {string} query - The search query string
 * @param {string} method - 'minhash', 'simhash', 'tfidf', or 'all'
 * @param {number} k - Number of results to retrieve (top-k)
 * @param {boolean} generateAnswer - Whether to generate an LLM answer
 */
export async function runQuery(query, method = 'all', k = 5, generateAnswer = true) {
  const { data } = await client.post('/query', { 
    query, 
    method, 
    k, 
    generate_answer: generateAnswer 
  })
  return data
}
