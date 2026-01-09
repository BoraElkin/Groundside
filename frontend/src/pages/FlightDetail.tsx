import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import FlightTimeline from '../components/FlightTimeline'
import StatusBadge from '../components/StatusBadge'
import { getFlight, getTurnaroundsByFlight } from '../services/api'

interface Flight {
  id: number
  flight_number: string
  airline_name: string
  aircraft_type: string
  origin_airport: string
  destination_airport: string
  scheduled_time: string
  status: string
  gate?: string
  departure_delay?: number
}

const FlightDetail = () => {
  const { id } = useParams<{ id: string }>()
  const [flight, setFlight] = useState<Flight | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      loadFlightDetail(parseInt(id))
    }
  }, [id])

  const loadFlightDetail = async (flightId: number) => {
    try {
      setLoading(true)
      const flightData = await getFlight(flightId)
      setFlight(flightData)
    } catch (error) {
      console.error('Failed to load flight detail:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ground-ops-600"></div>
      </div>
    )
  }

  if (!flight) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Flight not found</h1>
          <p className="mt-2 text-gray-600">The requested flight could not be found.</p>
          <a href="/" className="mt-4 inline-block text-ground-ops-600 hover:text-ground-ops-700">
            ← Back to Dashboard
          </a>
        </div>
      </div>
    )
  }

  // Mock timeline events
  const timelineEvents = [
    {
      id: '1',
      timestamp: flight.scheduled_time,
      title: 'Aircraft Arrival',
      status: 'completed' as const,
      description: 'Aircraft arrived at gate',
    },
    {
      id: '2',
      timestamp: new Date(new Date(flight.scheduled_time).getTime() + 10 * 60000).toISOString(),
      title: 'Passenger Deboarding',
      status: 'completed' as const,
    },
    {
      id: '3',
      timestamp: new Date(new Date(flight.scheduled_time).getTime() + 20 * 60000).toISOString(),
      title: 'Cleaning & Refueling',
      status: 'in_progress' as const,
    },
    {
      id: '4',
      timestamp: new Date(new Date(flight.scheduled_time).getTime() + 40 * 60000).toISOString(),
      title: 'Passenger Boarding',
      status: 'pending' as const,
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <div className="mb-6">
        <a
          href="/"
          className="inline-flex items-center text-sm text-ground-ops-600 hover:text-ground-ops-700"
        >
          <svg
            className="mr-2 h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          Back to Dashboard
        </a>
      </div>

      {/* Flight Header */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{flight.flight_number}</h1>
            <p className="mt-1 text-lg text-gray-600">{flight.airline_name}</p>
          </div>
          <StatusBadge status={flight.status as any} size="lg">
            {flight.status.toUpperCase()}
          </StatusBadge>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-500">Route</h3>
            <p className="mt-1 text-lg font-semibold text-gray-900">
              {flight.origin_airport} → {flight.destination_airport}
            </p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Aircraft</h3>
            <p className="mt-1 text-lg font-semibold text-gray-900">{flight.aircraft_type}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-500">Gate</h3>
            <p className="mt-1 text-lg font-semibold text-gray-900">{flight.gate || 'TBA'}</p>
          </div>
        </div>

        {flight.departure_delay && flight.departure_delay > 0 && (
          <div className="mt-4 p-4 bg-orange-50 rounded-md">
            <p className="text-sm text-orange-800">
              ⚠️ Current delay: <span className="font-semibold">{flight.departure_delay} minutes</span>
            </p>
          </div>
        )}
      </div>

      {/* Turnaround Timeline */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-6">Turnaround Progress</h2>
        <FlightTimeline events={timelineEvents} />
      </div>
    </div>
  )
}

export default FlightDetail
