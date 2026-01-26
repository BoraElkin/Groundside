import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getDispute,
  getDisputeStatus,
  analyzeDispute,
  regenerateResponse,
} from '../services/api'
import {
  DisputeDetail,
  DisputeStatus,
  DisputeActivity,
  DisputeState,
  ResponsibleParty,
} from '../types/dispute'

const DisputeDetailView = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [dispute, setDispute] = useState<DisputeDetail | null>(null)
  const [status, setStatus] = useState<DisputeStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [showActivityForm, setShowActivityForm] = useState(false)
  const [showEditor, setShowEditor] = useState(false)
  const [editedResponse, setEditedResponse] = useState('')
  const [feedback, setFeedback] = useState('')
  const [regenerating, setRegenerating] = useState(false)

  // Activity form state
  const [activities, setActivities] = useState<DisputeActivity[]>([
    {
      activity_type: 'deboarding',
      performed_by: ResponsibleParty.HANDLER,
      actual_start: '',
      actual_end: '',
      notes: '',
    },
  ])

  useEffect(() => {
    if (id) {
      loadDispute()
    }
  }, [id])

  useEffect(() => {
    // Poll status if processing
    if (
      status &&
      (status.state === DisputeState.ANALYZING ||
        status.state === DisputeState.GENERATING_RESPONSE ||
        status.state === DisputeState.EXTRACTING_DETAILS)
    ) {
      const interval = setInterval(() => {
        loadStatus()
      }, 2000) // Poll every 2 seconds

      return () => clearInterval(interval)
    }
  }, [status])

  const loadDispute = async () => {
    if (!id) return

    setLoading(true)
    try {
      const [disputeData, statusData] = await Promise.all([
        getDispute(id),
        getDisputeStatus(id),
      ])
      setDispute(disputeData)
      setStatus(statusData)
      setEditedResponse(disputeData.dispute_response_text || '')
    } catch (error) {
      console.error('Failed to load dispute:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStatus = async () => {
    if (!id) return
    try {
      const statusData = await getDisputeStatus(id)
      setStatus(statusData)

      // If processing complete, reload full dispute
      if (
        statusData.state === DisputeState.RESPONSE_GENERATED ||
        statusData.state === DisputeState.ANALYSIS_COMPLETE
      ) {
        loadDispute()
      }
    } catch (error) {
      console.error('Failed to load status:', error)
    }
  }

  const handleAddActivity = () => {
    setActivities([
      ...activities,
      {
        activity_type: '',
        performed_by: ResponsibleParty.HANDLER,
        actual_start: '',
        actual_end: '',
        notes: '',
      },
    ])
  }

  const handleActivityChange = (index: number, field: string, value: any) => {
    const updated = [...activities]
    updated[index] = { ...updated[index], [field]: value }
    setActivities(updated)
  }

  const handleRemoveActivity = (index: number) => {
    setActivities(activities.filter((_, i) => i !== index))
  }

  const handleSubmitActivities = async () => {
    if (!id) return

    try {
      await analyzeDispute(id, activities)
      setShowActivityForm(false)
      // Start polling for status
      loadStatus()
    } catch (error) {
      console.error('Failed to submit activities:', error)
      alert('Failed to submit activities. Please try again.')
    }
  }

  const handleRegenerateResponse = async () => {
    if (!id || !feedback) return

    setRegenerating(true)
    try {
      const updated = await regenerateResponse(id, feedback)
      setDispute({ ...dispute!, ...updated })
      setEditedResponse(updated.dispute_response_text || '')
      setFeedback('')
      setShowEditor(false)
    } catch (error) {
      console.error('Failed to regenerate:', error)
      alert('Failed to regenerate response. Please try again.')
    } finally {
      setRegenerating(false)
    }
  }

  const formatCurrency = (amount?: number, currency?: string) => {
    if (!amount) return '-'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(amount)
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getStateBadgeColor = (state: DisputeState) => {
    switch (state) {
      case DisputeState.RESPONSE_GENERATED:
      case DisputeState.APPROVED:
        return 'bg-green-100 text-green-800'
      case DisputeState.ANALYZING:
      case DisputeState.GENERATING_RESPONSE:
        return 'bg-blue-100 text-blue-800'
      case DisputeState.FAILED:
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!dispute) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-gray-500">Dispute not found</div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/disputes')}
          className="text-blue-600 hover:text-blue-700 mb-4 flex items-center"
        >
          ← Back to Disputes
        </button>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {dispute.flight_number || 'Dispute'}
            </h1>
            <p className="mt-2 text-gray-600">
              {formatDate(dispute.flight_date)} • {dispute.airline_code}
            </p>
          </div>
          <span
            className={`px-3 py-1 text-sm font-semibold rounded-full ${getStateBadgeColor(
              dispute.state
            )}`}
          >
            {dispute.state.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {/* Processing Status Bar */}
      {status && status.progress_percentage < 100 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-blue-900">{status.current_step}</div>
            <div className="text-sm text-blue-700">{status.progress_percentage}%</div>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${status.progress_percentage}%` }}
            ></div>
          </div>
          {status.estimated_completion_seconds && (
            <div className="text-xs text-blue-600 mt-2">
              Est. completion: {status.estimated_completion_seconds}s
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {dispute.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
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
            <div className="ml-3">
              <p className="text-sm text-red-800">{dispute.error_message}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Details */}
        <div className="lg:col-span-1 space-y-6">
          {/* Flight Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Flight Details</h2>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500">Flight Number</div>
                <div className="font-medium">{dispute.flight_number || '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Date</div>
                <div className="font-medium">{formatDate(dispute.flight_date)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Route</div>
                <div className="font-medium">
                  {dispute.origin && dispute.destination
                    ? `${dispute.origin} → ${dispute.destination}`
                    : '-'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Aircraft Type</div>
                <div className="font-medium">{dispute.aircraft_type || '-'}</div>
              </div>
            </div>
          </div>

          {/* Penalty Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Penalty Details</h2>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500">Penalty Amount</div>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(dispute.penalty_amount, dispute.penalty_currency)}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Claimed Delay</div>
                <div className="font-medium">{dispute.claimed_delay_minutes} minutes</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Airline's Reason</div>
                <div className="font-medium text-gray-700">
                  {dispute.airline_claimed_reason || '-'}
                </div>
              </div>
            </div>
          </div>

          {/* Analysis Summary */}
          {dispute.root_cause_analysis && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Analysis Summary
              </h2>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-500">Actual Delay</div>
                  <div className="font-medium">{dispute.actual_delay_minutes} minutes</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Handler Responsible</div>
                  <div className="font-medium">
                    {dispute.handler_responsible_minutes} minutes
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Confidence</div>
                  <div className="font-medium">
                    {dispute.confidence_score
                      ? `${(dispute.confidence_score * 100).toFixed(0)}%`
                      : '-'}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Recommendation</div>
                  <div className="font-medium capitalize">
                    {dispute.recommendation?.replace(/_/g, ' ') || '-'}
                  </div>
                </div>
                {dispute.iata_delay_codes && dispute.iata_delay_codes.length > 0 && (
                  <div>
                    <div className="text-sm text-gray-500">IATA Delay Codes</div>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {dispute.iata_delay_codes.map((code) => (
                        <span
                          key={code}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded"
                        >
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Activities & Response */}
        <div className="lg:col-span-2 space-y-6">
          {/* Activities Section */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900">
                  Turnaround Activities
                </h2>
                {dispute.state === DisputeState.DETAILS_EXTRACTED &&
                  !showActivityForm && (
                    <button
                      onClick={() => setShowActivityForm(true)}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium"
                    >
                      Add Activities
                    </button>
                  )}
              </div>
            </div>

            <div className="p-6">
              {showActivityForm ? (
                <div className="space-y-4">
                  {activities.map((activity, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Activity Type
                          </label>
                          <input
                            type="text"
                            value={activity.activity_type}
                            onChange={(e) =>
                              handleActivityChange(index, 'activity_type', e.target.value)
                            }
                            placeholder="e.g. deboarding, boarding, cleaning"
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Performed By
                          </label>
                          <select
                            value={activity.performed_by}
                            onChange={(e) =>
                              handleActivityChange(
                                index,
                                'performed_by',
                                e.target.value as ResponsibleParty
                              )
                            }
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                          >
                            <option value={ResponsibleParty.HANDLER}>Handler</option>
                            <option value={ResponsibleParty.AIRLINE}>Airline</option>
                            <option value={ResponsibleParty.VENDOR_CATERING}>
                              Catering
                            </option>
                            <option value={ResponsibleParty.VENDOR_FUEL}>Fuel</option>
                            <option value={ResponsibleParty.VENDOR_CLEANING}>
                              Cleaning
                            </option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Start Time
                          </label>
                          <input
                            type="datetime-local"
                            value={activity.actual_start}
                            onChange={(e) =>
                              handleActivityChange(index, 'actual_start', e.target.value)
                            }
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            End Time
                          </label>
                          <input
                            type="datetime-local"
                            value={activity.actual_end}
                            onChange={(e) =>
                              handleActivityChange(index, 'actual_end', e.target.value)
                            }
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                          />
                        </div>
                        <div className="col-span-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Notes
                          </label>
                          <input
                            type="text"
                            value={activity.notes}
                            onChange={(e) =>
                              handleActivityChange(index, 'notes', e.target.value)
                            }
                            placeholder="Any additional notes"
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                          />
                        </div>
                      </div>
                      {activities.length > 1 && (
                        <button
                          onClick={() => handleRemoveActivity(index)}
                          className="mt-2 text-red-600 hover:text-red-700 text-sm"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ))}

                  <div className="flex justify-between pt-4">
                    <button
                      onClick={handleAddActivity}
                      className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                    >
                      + Add Another Activity
                    </button>
                    <div className="space-x-2">
                      <button
                        onClick={() => setShowActivityForm(false)}
                        className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSubmitActivities}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium"
                      >
                        Submit & Analyze
                      </button>
                    </div>
                  </div>
                </div>
              ) : dispute.activities && dispute.activities.length > 0 ? (
                <div className="space-y-2">
                  {dispute.activities.map((activity) => (
                    <div
                      key={activity.id}
                      className="flex justify-between items-center py-2 border-b border-gray-100"
                    >
                      <div>
                        <div className="font-medium capitalize">
                          {activity.activity_type}
                        </div>
                        <div className="text-sm text-gray-500">
                          {activity.performed_by} •{' '}
                          {activity.actual_duration_minutes || '-'} min
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        {formatDate(activity.actual_start)} -{' '}
                        {formatDate(activity.actual_end)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  No activities added yet. Add activities to start analysis.
                </div>
              )}
            </div>
          </div>

          {/* Response Section */}
          {dispute.dispute_response_text && (
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Dispute Response Letter
                  </h2>
                  <button
                    onClick={() => setShowEditor(!showEditor)}
                    className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 text-sm font-medium"
                  >
                    {showEditor ? 'View' : 'Edit'}
                  </button>
                </div>
              </div>

              <div className="p-6">
                {showEditor ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Feedback for Regeneration
                      </label>
                      <textarea
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        rows={3}
                        placeholder="e.g. Make it more formal, add more emphasis on IATA codes..."
                        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <button
                      onClick={handleRegenerateResponse}
                      disabled={!feedback || regenerating}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {regenerating ? 'Regenerating...' : 'Regenerate Response'}
                    </button>
                  </div>
                ) : (
                  <div className="prose max-w-none">
                    <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700">
                      {dispute.dispute_response_text}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DisputeDetailView
