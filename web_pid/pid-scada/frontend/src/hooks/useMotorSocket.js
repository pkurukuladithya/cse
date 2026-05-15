import { useEffect, useRef, useCallback } from 'react'
import { useScadaStore } from '../store/useScadaStore'

const WS_URL = `ws://${window.location.host}/ws`

export function useMotorSocket() {
  const wsRef = useRef(null)
  const retryCount = useRef(0)
  const reconnectTimeout = useRef(null)
  
  const setWsStatus = useScadaStore(s => s.setWsStatus)
  const updateTelemetry = useScadaStore(s => s.updateTelemetry)
  const pushTrendData = useScadaStore(s => s.pushTrendData)
  const addAlarm = useScadaStore(s => s.addAlarm)
  const updateTuneProgress = useScadaStore(s => s.updateTuneProgress)
  const setTuneResult = useScadaStore(s => s.setTuneResult)
  const setSendCommand = useScadaStore(s => s.setSendCommand)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return

    setWsStatus('connecting')
    
    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        setWsStatus('connected')
        retryCount.current = 0
        console.log('WS connected')
      }

      ws.onmessage = (evt) => {
        try {
          const { type, data } = JSON.parse(evt.data)

          switch (type) {
            case 'telemetry':
              updateTelemetry(data)
              pushTrendData({
                time: new Date(data.ts * 1000).toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'}),
                rpm: data.rpm,
                setpoint: data.setpoint
              })
              break
            case 'alarm':
              addAlarm(data)
              break
            case 'autotune_progress':
              updateTuneProgress(data)
              break
            case 'autotune_result':
              setTuneResult(data)
              break
            default:
              console.warn('Unknown WS message type:', type)
          }
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }

      ws.onclose = () => {
        setWsStatus('disconnected')
        // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
        const backoff = Math.min(1000 * Math.pow(2, retryCount.current), 30000)
        retryCount.current++
        
        console.log(`WS closed, reconnecting in ${backoff}ms...`)
        clearTimeout(reconnectTimeout.current)
        reconnectTimeout.current = setTimeout(connect, backoff)
      }

      ws.onerror = (err) => {
        console.error('WS Error:', err)
        ws.close()
      }

    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setWsStatus('disconnected')
      const backoff = Math.min(1000 * Math.pow(2, retryCount.current), 30000)
      retryCount.current++
      reconnectTimeout.current = setTimeout(connect, backoff)
    }
  }, [setWsStatus, updateTelemetry, pushTrendData, addAlarm, updateTuneProgress, setTuneResult])

  // Setup sendCommand once
  useEffect(() => {
    const send = (action, params = {}) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action, params }))
      } else {
        console.warn('Cannot send command, WS not open:', action)
      }
    }
    setSendCommand(send)
  }, [setSendCommand])

  // Connect on mount
  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimeout.current)
      if (wsRef.current) {
        wsRef.current.onclose = null // prevent reconnect loop on unmount
        wsRef.current.close()
      }
    }
  }, [connect])
}
