/**
 * useMotorSocket.js
 * Custom React hook — connects to the FastAPI WebSocket and
 * exposes live motor state to all components.
 */
import { useState, useEffect, useRef, useCallback } from 'react'

const WS_URL = `ws://${window.location.host}/ws`

const DEFAULT_STATE = {
  target_rpm:    0,
  actual_rpm:    0,
  smoothed_rpm:  0,
  pwm:           0,
  overshoot:     0,
  sse:           0,
  settling_time: 0,
  Kp:            1.5,
  Ki:            1.5,
  Kd:            0.0,
  running:       false,
  alarm:         null,
  autotune: {
    active: false, status: 'IDLE', progress: 0, result: null, log: []
  }
}

export function useMotorSocket() {
  const [motorState, setMotorState] = useState(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const [trendData, setTrendData] = useState([])   // rolling 120-point buffer
  const wsRef     = useRef(null)
  const retryRef  = useRef(null)
  const tickRef   = useRef(0)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      clearTimeout(retryRef.current)
    }

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        setMotorState(data)

        tickRef.current++
        setTrendData(prev => {
          const next = [...prev, {
            t:       tickRef.current,
            setpt:   data.target_rpm,
            smooth:  data.smoothed_rpm,
            raw:     data.actual_rpm,
          }]
          return next.length > 120 ? next.slice(-120) : next
        })
      } catch (_) {}
    }

    ws.onclose = () => {
      setConnected(false)
      // Auto-reconnect after 2s
      retryRef.current = setTimeout(connect, 2000)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(retryRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  // ── Send update to backend ──────────────────
  const sendUpdate = useCallback(async (patch) => {
    try {
      await fetch('/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      })
    } catch (_) {}
  }, [])

  return { motorState, connected, trendData, sendUpdate }
}
