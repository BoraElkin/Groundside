import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Flights API
export const getFlights = async (params?: any) => {
  const response = await api.get('/flights/', { params })
  return response.data
}

export const getFlight = async (id: number) => {
  const response = await api.get(`/flights/${id}`)
  return response.data
}

export const createFlight = async (data: any) => {
  const response = await api.post('/flights/', data)
  return response.data
}

export const updateFlight = async (id: number, data: any) => {
  const response = await api.patch(`/flights/${id}`, data)
  return response.data
}

export const getDelayedFlights = async (thresholdMinutes = 15) => {
  const response = await api.get('/flights/delayed/list', {
    params: { threshold_minutes: thresholdMinutes },
  })
  return response.data
}

// Turnarounds API
export const getTurnarounds = async (params?: any) => {
  const response = await api.get('/turnarounds/', { params })
  return response.data
}

export const getTurnaround = async (id: number) => {
  const response = await api.get(`/turnarounds/${id}`)
  return response.data
}

export const getTurnaroundsByFlight = async (flightId: number) => {
  const response = await api.get(`/turnarounds/flight/${flightId}`)
  return response.data
}

export const createTurnaround = async (data: any) => {
  const response = await api.post('/turnarounds/', data)
  return response.data
}

export const updateTurnaround = async (id: number, data: any) => {
  const response = await api.patch(`/turnarounds/${id}`, data)
  return response.data
}

export const getAtRiskTurnarounds = async (riskThreshold = 0.5) => {
  const response = await api.get('/turnarounds/at-risk/list', {
    params: { risk_threshold: riskThreshold },
  })
  return response.data
}

export const getActiveTurnaroundsDashboard = async () => {
  const response = await api.get('/turnarounds/active/dashboard')
  return response.data
}

// Alerts API
export const getAlerts = async (params?: any) => {
  const response = await api.get('/alerts/', { params })
  return response.data
}

export const getAlert = async (id: number) => {
  const response = await api.get(`/alerts/${id}`)
  return response.data
}

export const createAlert = async (data: any) => {
  const response = await api.post('/alerts/', data)
  return response.data
}

export const updateAlert = async (id: number, data: any) => {
  const response = await api.patch(`/alerts/${id}`, data)
  return response.data
}

export const acknowledgeAlert = async (id: number, acknowledgedBy: string) => {
  const response = await api.post(`/alerts/${id}/acknowledge`, null, {
    params: { acknowledged_by: acknowledgedBy },
  })
  return response.data
}

export const resolveAlert = async (id: number, resolvedBy: string, notes?: string) => {
  const response = await api.post(`/alerts/${id}/resolve`, null, {
    params: { resolved_by: resolvedBy, resolution_notes: notes },
  })
  return response.data
}

export const getActiveAlerts = async (severity?: string) => {
  const response = await api.get('/alerts/active/list', {
    params: severity ? { severity } : undefined,
  })
  return response.data
}

export const getCriticalAlerts = async (hours = 24) => {
  const response = await api.get('/alerts/critical/recent', {
    params: { hours },
  })
  return response.data
}

// Analytics API
export const getDelayStatistics = async (hours = 24, airline?: string) => {
  const response = await api.get('/analytics/delays', {
    params: { hours, airline },
  })
  return response.data
}

export const getTurnaroundStatistics = async (hours = 24, gate?: string) => {
  const response = await api.get('/analytics/turnarounds', {
    params: { hours, gate },
  })
  return response.data
}

export const getDashboardSummary = async () => {
  const response = await api.get('/analytics/dashboard/summary')
  return response.data
}

export const getHourlyPerformance = async (hours = 24) => {
  const response = await api.get('/analytics/performance/hourly', {
    params: { hours },
  })
  return response.data
}

export default api
