import client from './client'

/**
 * Fetch combined experiment results.
 * @param {{ refresh?: boolean }} [options]
 */
export async function getExperiments(options = {}) {
  const { refresh = false } = options
  const { data } = await client.get('/experiments/', {
    params: { refresh },
    timeout: 240000,
  })
  return data
}
