import { formatDistanceToNow } from 'date-fns'
import StatusBadge from './StatusBadge'
import clsx from 'clsx'

interface Activity {
  activity_type: string
  activity_name: string
  status: string
  progress_percentage: number
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
  activities?: Activity[]
}

interface TurnaroundCardProps {
  turnaround: Turnaround
  onClick?: () => void
}

const TurnaroundCard = ({ turnaround, onClick }: TurnaroundCardProps) => {
  const getStatusType = (status: string, riskScore: number) => {
    if (status === 'delayed' || status === 'critical') return 'critical'
    if (status === 'at_risk' || riskScore > 0.7) return 'at-risk'
    if (status === 'on_time') return 'on-time'
    return 'info'
  }

  const getBorderColor = (status: string, riskScore: number) => {
    if (status === 'delayed' || riskScore > 0.8) return 'border-red-500'
    if (status === 'at_risk' || riskScore > 0.6) return 'border-yellow-500'
    return 'border-green-500'
  }

  const statusType = getStatusType(turnaround.status, turnaround.risk_score)
  const borderColor = getBorderColor(turnaround.status, turnaround.risk_score)

  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-md p-6 border-l-4 transition-all hover:shadow-lg cursor-pointer',
        borderColor
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {turnaround.flight_number || turnaround.turnaround_id}
          </h3>
          <p className="text-sm text-gray-500">Gate {turnaround.gate || 'TBA'}</p>
        </div>
        <StatusBadge status={statusType}>
          {turnaround.status.replace('_', ' ').toUpperCase()}
        </StatusBadge>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{Math.round(turnaround.completion_percentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={clsx(
              'h-2.5 rounded-full',
              statusType === 'critical' ? 'bg-red-600' :
              statusType === 'at-risk' ? 'bg-yellow-500' :
              'bg-green-600'
            )}
            style={{ width: `${turnaround.completion_percentage}%` }}
          ></div>
        </div>
      </div>

      {/* Timing Info */}
      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
        <div>
          <p className="text-gray-500">Scheduled</p>
          <p className="font-medium text-gray-900">
            {formatDistanceToNow(new Date(turnaround.scheduled_start), { addSuffix: true })}
          </p>
        </div>
        {turnaround.estimated_completion && (
          <div>
            <p className="text-gray-500">Estimated Completion</p>
            <p className="font-medium text-gray-900">
              {formatDistanceToNow(new Date(turnaround.estimated_completion), { addSuffix: true })}
            </p>
          </div>
        )}
      </div>

      {/* Risk Score */}
      {turnaround.risk_score > 0.5 && (
        <div className="flex items-center text-sm">
          <svg
            className="h-4 w-4 text-yellow-500 mr-1"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-gray-700">
            Risk Score: <span className="font-semibold">{(turnaround.risk_score * 100).toFixed(0)}%</span>
          </span>
        </div>
      )}

      {/* Predicted Delay */}
      {turnaround.predicted_delay && turnaround.predicted_delay > 0 && (
        <div className="mt-2 text-sm text-orange-600 font-medium">
          ⚠️ Predicted delay: {turnaround.predicted_delay} minutes
        </div>
      )}

      {/* Activities Summary */}
      {turnaround.activities && turnaround.activities.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2">Active Activities</p>
          <div className="flex flex-wrap gap-1">
            {turnaround.activities
              .filter(a => a.status === 'in_progress')
              .slice(0, 3)
              .map((activity, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {activity.activity_name}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default TurnaroundCard
