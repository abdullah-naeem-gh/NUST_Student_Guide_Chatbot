import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Shared Axios instance for the FastAPI backend.
 */
const client = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

export default client
