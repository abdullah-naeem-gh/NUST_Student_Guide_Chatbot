import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import QueryPage from './pages/QueryPage'
import IngestPage from './pages/IngestPage'
import AnalyticsPage from './pages/AnalyticsPage'
import useAppStore from './store/appStore'

function App() {
  const { darkMode } = useAppStore()

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    document.body.classList.toggle('light', !darkMode)
    document.body.classList.add('theme-guide')
  }, [darkMode])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<QueryPage />} />
        <Route path="/chat" element={<QueryPage initialScreen="chat" />} />
        <Route path="/ingest" element={<IngestPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </Router>
  )
}

export default App
