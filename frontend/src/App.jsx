import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Analyze from './pages/Analyze'
import Tracker from './pages/Tracker'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 px-6 py-3 flex gap-6 text-sm">
          <span className="font-bold text-green-400 mr-4">EdgeIQ</span>
          <NavLink to="/" className={({ isActive }) =>
            isActive ? 'text-green-400' : 'text-gray-400 hover:text-gray-200'}>
            Analyze
          </NavLink>
          <NavLink to="/tracker" className={({ isActive }) =>
            isActive ? 'text-green-400' : 'text-gray-400 hover:text-gray-200'}>
            Tracker
          </NavLink>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">
          <Routes>
            <Route path="/" element={<Analyze />} />
            <Route path="/tracker" element={<Tracker />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
