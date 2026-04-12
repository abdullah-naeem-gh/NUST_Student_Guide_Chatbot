import client from './client'

/**
 * GET /ping — backend health and index readiness.
 * @returns {Promise<{ status: string, indexed: boolean }>}
 */
export async function ping() {
  const { data } = await client.get('/ping')
  return data
}
