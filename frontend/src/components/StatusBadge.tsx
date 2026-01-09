import { ReactNode } from 'react'
import clsx from 'clsx'

type StatusType = 'on-time' | 'at-risk' | 'delayed' | 'critical' | 'info' | 'warning'

interface StatusBadgeProps {
  status: StatusType
  children: ReactNode
  size?: 'sm' | 'md' | 'lg'
}

const StatusBadge = ({ status, children, size = 'md' }: StatusBadgeProps) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-full'

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  }

  const statusClasses = {
    'on-time': 'bg-green-100 text-green-800',
    'at-risk': 'bg-yellow-100 text-yellow-800',
    'delayed': 'bg-orange-100 text-orange-800',
    'critical': 'bg-red-100 text-red-800',
    'info': 'bg-blue-100 text-blue-800',
    'warning': 'bg-yellow-100 text-yellow-800',
  }

  return (
    <span className={clsx(baseClasses, sizeClasses[size], statusClasses[status])}>
      {children}
    </span>
  )
}

export default StatusBadge
