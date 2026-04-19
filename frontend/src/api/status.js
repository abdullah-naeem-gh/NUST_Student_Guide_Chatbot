import client from './client'

export async function getStatus() {
  const { data } = await client.get('/status')
  return data
}
