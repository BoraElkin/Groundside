import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import FlightDetail from './pages/FlightDetail'
import Analytics from './pages/Analytics'
import DisputeDashboard from './pages/DisputeDashboard'
import NewDispute from './pages/NewDispute'
import DisputeDetail from './pages/DisputeDetail'

function App() {
  const currentPath = window.location.pathname

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-blue-700">
                  GroundCrew AI
                </h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <a
                  href="/"
                  className={`${
                    currentPath === '/'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  Operations
                </a>
                <a
                  href="/disputes"
                  className={`${
                    currentPath.startsWith('/disputes')
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  Disputes
                </a>
                <a
                  href="/analytics"
                  className={`${
                    currentPath === '/analytics'
                      ? 'border-blue-500 text-gray-900'
                      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                  } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                >
                  Analytics
                </a>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/flight/:id" element={<FlightDetail />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/disputes" element={<DisputeDashboard />} />
          <Route path="/disputes/new" element={<NewDispute />} />
          <Route path="/disputes/:id" element={<DisputeDetail />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
