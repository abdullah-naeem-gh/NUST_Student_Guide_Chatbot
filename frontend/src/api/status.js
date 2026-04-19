import client from './client'

/**
 * Normalize GET /status payload for UI (backend uses indexed/chunk_count).
 * @returns {Promise<{ is_indexed: boolean, num_chunks: number, source_file: string, source_files: string[], last_updated: null, [key: string]: unknown }>}
 */
export async function getStatus() {
  const { data } = await client.get('/status')
  return {
    ...data,
    is_indexed: data.indexed ?? data.is_indexed ?? false,
    num_chunks: data.chunk_count ?? data.num_chunks ?? 0,
    source_file: data.source_file ?? '',
    source_files: Array.isArray(data.source_files) ? data.source_files : [],
    last_updated: data.last_updated ?? null,
  }
}
