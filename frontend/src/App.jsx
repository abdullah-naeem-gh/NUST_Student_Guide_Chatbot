import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import QueryPage from './pages/QueryPage'
import IngestPage from './pages/IngestPage'
import useAppStore from './store/appStore'
import { useEffect } from 'react'

function App() {
  const { darkMode } = useAppStore()

  useEffect(() => {
    // Sync dark mode on mount
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<QueryPage />} />
        <Route path="/ingest" element={<IngestPage />} />
      </Routes>
    </Router>
  )
}

export default App
