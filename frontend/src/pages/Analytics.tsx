import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { getDelayStatistics, getTurnaroundStatistics } from '../services/api'

const Analytics = () => {
  const [delayStats, setDelayStats] = useState({
    total_flights: 0,
    delayed_flights: 0,
    average_delay_minutes: 0,
    on_time_percentage: 0,
  })

  const [turnaroundStats, setTurnaroundStats] = useState({
    total_turnarounds: 0,
    completed_on_time: 0,
    at_risk: 0,
    delayed: 0,
    average_duration_minutes: 0,
  })

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAnalytics()
  }, [])

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      const [delays, turnarounds] = await Promise.all([
        getDelayStatistics(24),
        getTurnaroundStatistics(24),
      ])
      setDelayStats(delays)
      setTurnaroundStats(turnarounds)
    } catch (error) {
      console.error('Failed to load analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  // Mock hourly data
  const hourlyData = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    flights: Math.floor(Math.random() * 20) + 5,
    delays: Math.floor(Math.random() * 8),
  }))

  // Mock delay distribution
  const delayDistribution = [
    { range: '0-15 min', count: 45 },
    { range: '15-30 min', count: 23 },
    { range: '30-60 min', count: 12 },
    { range: '60+ min', count: 5 },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ground-ops-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Analytics & Insights</h1>
        <p className="mt-2 text-sm text-gray-600">Performance metrics for the last 24 hours</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Total Flights</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{delayStats.total_flights}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">On-Time Performance</h3>
          <p className="mt-2 text-3xl font-semibold text-green-600">
            {delayStats.on_time_percentage.toFixed(1)}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Avg Delay</h3>
          <p className="mt-2 text-3xl font-semibold text-orange-600">
            {delayStats.average_delay_minutes.toFixed(0)} min
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500">Avg Turnaround</h3>
          <p className="mt-2 text-3xl font-semibold text-blue-600">
            {turnaroundStats.average_duration_minutes.toFixed(0)} min
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Flight Volume */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Hourly Flight Volume</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="flights" stroke="#0ea5e9" name="Total Flights" />
              <Line type="monotone" dataKey="delays" stroke="#f97316" name="Delayed" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Delay Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Delay Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={delayDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#0ea5e9" name="Flights" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Turnaround Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Turnaround Status</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Completed On Time</span>
              <span className="text-2xl font-semibold text-green-600">
                {turnaroundStats.completed_on_time}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">At Risk</span>
              <span className="text-2xl font-semibold text-yellow-600">
                {turnaroundStats.at_risk}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Delayed</span>
              <span className="text-2xl font-semibold text-red-600">
                {turnaroundStats.delayed}
              </span>
            </div>
          </div>
        </div>

        {/* Performance Summary */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Performance Summary</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>On-Time Rate</span>
                <span>{delayStats.on_time_percentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-green-600 h-2.5 rounded-full"
                  style={{ width: `${delayStats.on_time_percentage}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Delay Rate</span>
                <span>
                  {((delayStats.delayed_flights / delayStats.total_flights) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-orange-600 h-2.5 rounded-full"
                  style={{
                    width: `${(delayStats.delayed_flights / delayStats.total_flights) * 100}%`,
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
