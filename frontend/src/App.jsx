import { BrowserRouter, Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage'

/**
 * Root router — placeholder routes until Phase 6.
 */
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  )
}
