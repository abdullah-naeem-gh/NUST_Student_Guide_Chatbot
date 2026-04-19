import client from './client'

export async function ingestFiles(files) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })

  const { data } = await client.post('/ingest/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return data
}

export async function startIndexing() {
  const { data } = await client.post('/ingest/index')
  return data
}
