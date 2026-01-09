import { useEffect, useState } from 'react'
import TurnaroundCard from '../components/TurnaroundCard'
import AlertBanner from '../components/AlertBanner'
import { useWebSocket } from '../hooks/useWebSocket'
import { getTurnarounds, getActiveAlerts } from '../services/api'

interface Alert {
  id: number
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
}

interface Turnaround {
  id: number
  turnaround_id: string
  status: string
  flight_number?: string
  gate?: string
  scheduled_start: string
  scheduled_end: string
  estimated_completion?: string
  predicted_delay?: number
  risk_score: number
  completion_percentage: number
}

const Dashboard = () => {
  const [turnarounds, setTurnarounds] = useState<Turnaround[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    active_turnarounds: 0,
    at_risk: 0,
    on_time: 0,
    delayed: 0,
  })

  // WebSocket connection for real-time updates
  const { lastMessage } = useWebSocket('ws://localhost:8000/ws')

  useEffect(() => {
    loadDashboardData()
  }, [])

  useEffect(() => {
    if (lastMessage) {
      // Handle real-time updates
      const data = JSON.parse(lastMessage.data)
      if (data.type === 'turnaround_update') {
        loadDashboardData() // Refresh data
      }
    }
  }, [lastMessage])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      // Load turnarounds and alerts in parallel
      const [turnaroundsData, alertsData] = await Promise.all([
        getTurnarounds({ status: 'active' }),
        getActiveAlerts(),
      ])

      setTurnarounds(turnaroundsData)
      setAlerts(alertsData)

      // Calculate stats
      const stats = {
        active_turnarounds: turnaroundsData.length,
        at_risk: turnaroundsData.filter((t: Turnaround) => t.status === 'at_risk').length,
        on_time: turnaroundsData.filter((t: Turnaround) => t.status === 'on_time').length,
        delayed: turnaroundsData.filter((t: Turnaround) => t.status === 'delayed').length,
      }
      setStats(stats)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const dismissAlert = (alertId: number) => {
    setAlerts(alerts.filter(a => a.id !== alertId))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ground-ops-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Operations Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Real-time monitoring of aircraft turnarounds at Istanbul Airport
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Active Turnarounds</dt>
                  <dd className="text-3xl font-semibold text-gray-900">{stats.active_turnarounds}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-green-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">On Time</dt>
                  <dd className="text-3xl font-semibold text-green-600">{stats.on_time}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-yellow-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">At Risk</dt>
                  <dd className="text-3xl font-semibold text-yellow-600">{stats.at_risk}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-red-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Delayed</dt>
                  <dd className="text-3xl font-semibold text-red-600">{stats.delayed}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.length > 0 && (
        <div className="mb-8 space-y-4">
          <h2 className="text-lg font-medium text-gray-900">Active Alerts</h2>
          {alerts.map(alert => (
            <AlertBanner
              key={alert.id}
              severity={alert.severity}
              title={alert.title}
              message={alert.message}
              onDismiss={() => dismissAlert(alert.id)}
            />
          ))}
        </div>
      )}

      {/* Turnarounds Grid */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Active Turnarounds</h2>
        {turnarounds.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No active turnarounds</h3>
            <p className="mt-1 text-sm text-gray-500">All turnarounds completed or none scheduled.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {turnarounds.map(turnaround => (
              <TurnaroundCard
                key={turnaround.id}
                turnaround={turnaround}
                onClick={() => (window.location.href = `/flight/${turnaround.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
