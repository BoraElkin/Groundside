import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getDisputes, getDisputeStats } from '../services/api'
import { Dispute, DisputeStats, DisputeState } from '../types/dispute'

const DisputeDashboard = () => {
  const [disputes, setDisputes] = useState<Dispute[]>([])
  const [stats, setStats] = useState<DisputeStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<DisputeState | 'all'>('all')

  useEffect(() => {
    loadData()
  }, [filter])

  const loadData = async () => {
    setLoading(true)
    try {
      const [disputesData, statsData] = await Promise.all([
        getDisputes({ state: filter !== 'all' ? filter : undefined }),
        getDisputeStats(),
      ])
      setDisputes(disputesData)
      setStats(statsData)
    } catch (error) {
      console.error('Failed to load disputes:', error)
    } finally {
      setLoading(false)
    }
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
      case DisputeState.UNDER_REVIEW:
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getRecommendationBadgeColor = (recommendation?: string) => {
    switch (recommendation) {
      case 'full_dispute':
        return 'bg-green-100 text-green-800'
      case 'partial_dispute':
        return 'bg-yellow-100 text-yellow-800'
      case 'accept_penalty':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
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
    })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dispute Resolution</h1>
            <p className="mt-2 text-gray-600">
              AI-powered dispute resolution for ground handler penalties
            </p>
          </div>
          <Link
            to="/disputes/new"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
          >
            + New Dispute
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Total Disputes</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_disputes}</div>
            <div className="text-sm text-gray-500 mt-1">
              {stats.disputes_this_month} this month
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Win Rate</div>
            <div className="text-3xl font-bold text-green-600">
              {stats.win_rate_percentage.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 mt-1">Success rate</div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Total Savings</div>
            <div className="text-3xl font-bold text-green-600">
              {formatCurrency(stats.total_savings)}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              From {formatCurrency(stats.total_penalties_claimed)} claimed
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500 mb-2">Avg Time</div>
            <div className="text-3xl font-bold text-blue-600">
              {stats.avg_time_to_resolve_minutes.toFixed(1)}m
            </div>
            <div className="text-sm text-gray-500 mt-1">To resolve</div>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Filter by state:</label>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as DisputeState | 'all')}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All States</option>
            <option value={DisputeState.DETAILS_EXTRACTED}>Details Extracted</option>
            <option value={DisputeState.EVIDENCE_GATHERED}>Evidence Gathered</option>
            <option value={DisputeState.ANALYZING}>Analyzing</option>
            <option value={DisputeState.RESPONSE_GENERATED}>Response Generated</option>
            <option value={DisputeState.UNDER_REVIEW}>Under Review</option>
            <option value={DisputeState.APPROVED}>Approved</option>
            <option value={DisputeState.FAILED}>Failed</option>
          </select>
        </div>
      </div>

      {/* Disputes List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500">Loading disputes...</div>
        ) : disputes.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No disputes found. Create your first dispute to get started.
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Flight
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Penalty
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Delay
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Recommendation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Confidence
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {disputes.map((dispute) => (
                <tr
                  key={dispute.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => (window.location.href = `/disputes/${dispute.id}`)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {dispute.flight_number || '-'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {dispute.airline_code || '-'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(dispute.flight_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {formatCurrency(dispute.penalty_amount, dispute.penalty_currency)}
                    </div>
                    {dispute.savings_amount && (
                      <div className="text-sm text-green-600">
                        Saved: {formatCurrency(dispute.savings_amount)}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {dispute.claimed_delay_minutes || '-'} min
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {dispute.recommendation ? (
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getRecommendationBadgeColor(
                          dispute.recommendation
                        )}`}
                      >
                        {dispute.recommendation.replace('_', ' ')}
                      </span>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStateBadgeColor(
                        dispute.state
                      )}`}
                    >
                      {dispute.state.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {dispute.confidence_score
                      ? `${(dispute.confidence_score * 100).toFixed(0)}%`
                      : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default DisputeDashboard
