import { useEffect, useState } from 'react'
import { useScadaStore } from '../../store/useScadaStore'

export default function Header() {
  const wsStatus = useScadaStore(s => s.wsStatus)
  const telemetry = useScadaStore(s => s.telemetry)
  const [clock, setClock] = useState('00:00:00')

  useEffect(() => {
    const timer = setInterval(() => {
      setClock(new Date().toLocaleTimeString('en-GB'))
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <header className="header">
      <div className="header-logo">
        <div className="logo-icon">⟳</div>
        <div>
          <div className="logo-title">Industrial SCADA &middot; PID Control System</div>
          <div className="logo-sub">Node: RPI4-B01 &middot; TB6612FNG Driver &middot; N20 Encoder Motor &middot; 5.28 V PSU</div>
        </div>
      </div>

      <div className="header-status">
        <div className="status-pill">
          <div className={`status-dot ${wsStatus === 'connected' ? 'connected' : ''}`} />
          <span>{wsStatus === 'connected' ? 'WS LIVE' : 'OFFLINE'}</span>
        </div>
        <div className="status-pill">
          <span style={{ color: telemetry.running ? 'var(--green)' : 'var(--red)' }}>
            {telemetry.running ? '▶ RUNNING' : '■ STOPPED'}
          </span>
        </div>
        <div className="header-time">{clock}</div>
      </div>
    </header>
  )
}
