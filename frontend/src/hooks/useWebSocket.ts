import { useEffect, useRef, useState } from 'react'

interface UseWebSocketOptions {
  reconnectInterval?: number
  reconnectAttempts?: number
}

interface UseWebSocketReturn {
  lastMessage: MessageEvent | null
  readyState: number
  sendMessage: (data: any) => void
}

export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const { reconnectInterval = 3000, reconnectAttempts = 10 } = options

  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null)
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef<number>(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = () => {
    try {
      const ws = new WebSocket(url)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setReadyState(WebSocket.OPEN)
        reconnectCountRef.current = 0
      }

      ws.onmessage = (event: MessageEvent) => {
        setLastMessage(event)
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setReadyState(WebSocket.CLOSED)

        // Attempt reconnection
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1
          console.log(
            `Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`
          )

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        }
      }

      wsRef.current = ws
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [url])

  const sendMessage = (data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected. Cannot send message.')
    }
  }

  return {
    lastMessage,
    readyState,
    sendMessage,
  }
}

export default useWebSocket
