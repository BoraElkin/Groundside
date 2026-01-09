import { format } from 'date-fns'
import clsx from 'clsx'

interface TimelineEvent {
  id: string
  timestamp: string
  title: string
  description?: string
  status: 'completed' | 'in_progress' | 'pending' | 'delayed'
}

interface FlightTimelineProps {
  events: TimelineEvent[]
}

const FlightTimeline = ({ events }: FlightTimelineProps) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'in_progress':
        return 'bg-blue-500'
      case 'delayed':
        return 'bg-red-500'
      case 'pending':
        return 'bg-gray-300'
      default:
        return 'bg-gray-300'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )
      case 'in_progress':
        return (
          <svg className="h-5 w-5 text-white animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )
      case 'delayed':
        return (
          <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495z"
              clipRule="evenodd"
            />
          </svg>
        )
      default:
        return <div className="h-3 w-3 rounded-full bg-white" />
    }
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {events.map((event, eventIdx) => (
          <li key={event.id}>
            <div className="relative pb-8">
              {eventIdx !== events.length - 1 && (
                <span
                  className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                  aria-hidden="true"
                />
              )}
              <div className="relative flex items-start space-x-3">
                <div>
                  <div
                    className={clsx(
                      'h-10 w-10 rounded-full flex items-center justify-center ring-8 ring-white',
                      getStatusColor(event.status)
                    )}
                  >
                    {getStatusIcon(event.status)}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div>
                    <div className="text-sm">
                      <span className="font-medium text-gray-900">{event.title}</span>
                    </div>
                    <p className="mt-0.5 text-sm text-gray-500">
                      {format(new Date(event.timestamp), 'HH:mm:ss')}
                    </p>
                  </div>
                  {event.description && (
                    <div className="mt-2 text-sm text-gray-700">
                      <p>{event.description}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default FlightTimeline
