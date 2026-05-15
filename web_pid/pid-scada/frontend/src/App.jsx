/**
 * App.jsx
 * Root component — header, nav tabs, tab routing.
 */
import { useState, useEffect } from 'react'
import { useMotorSocket } from './hooks/useMotorSocket'
import LiveDashboard   from './components/LiveDashboard'
import PIDPanel        from './components/PIDPanel'
import AutoTuneWizard  from './components/AutoTuneWizard'
import AlarmLog        from './components/AlarmLog'
import RunHistory      from './components/RunHistory'

const TABS = [
  { id: 'dashboard',  label: 'Live Dashboard',  icon: '◉' },
  { id: 'pid',        label: 'PID Tuning',       icon: '⚙' },
  { id: 'autotune',   label: 'Auto-Tune',        icon: '⚡' },
  { id: 'history',    label: 'Run History',      icon: '📊' },
  { id: 'alarms',     label: 'Alarms',           icon: '🔔', badge: true },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [clock, setClock]         = useState('')
  const { motorState, connected, trendData, sendUpdate } = useMotorSocket()

  // Live clock
  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('en-GB'))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [])

  // Alarm count for badge
  const [alarmCount, setAlarmCount] = useState(0)
  useEffect(() => {
    fetch('/api/alarms?limit=50')
      .then(r => r.json())
      .then(d => setAlarmCount(d.filter(a => a.level === 'CRITICAL').length))
      .catch(() => {})
  }, [])

  return (
    <div className="scada-root">

      {/* ── Header ───────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <div className="logo-icon">⟳</div>
          <div>
            <div className="h1">Industrial PID SCADA</div>
            <div className="sub">N20 Motor · TB6612 · RPi 4</div>
          </div>
        </div>

        <div className="header-status">
          <div className="status-pill">
            <div className={`status-dot ${connected ? 'connected' : ''}`} />
            <span>{connected ? 'WS LIVE' : 'CONNECTING…'}</span>
          </div>
          <div className="status-pill">
            <span style={{ color: motorState.running ? '#10b981' : '#ef4444' }}>
              {motorState.running ? '▶ RUNNING' : '■ STOPPED'}
            </span>
          </div>
          <div className="status-pill">
            <span style={{ color: '#f59e0b' }}>{motorState.smoothed_rpm?.toFixed(1)} RPM</span>
          </div>
          <span className="header-time">{clock}</span>
        </div>
      </header>

      {/* ── Nav Tabs ─────────────────────────── */}
      <nav className="nav-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`nav-tab ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            <span>{t.icon}</span>
            {t.label}
            {t.badge && alarmCount > 0 && (
              <span className="tab-badge">{alarmCount}</span>
            )}
          </button>
        ))}
      </nav>

      {/* ── Page Content ─────────────────────── */}
      <main className="main-content">
        {activeTab === 'dashboard' && (
          <LiveDashboard
            motorState={motorState}
            trendData={trendData}
            sendUpdate={sendUpdate}
          />
        )}
        {activeTab === 'pid' && (
          <PIDPanel
            motorState={motorState}
            sendUpdate={sendUpdate}
          />
        )}
        {activeTab === 'autotune' && (
          <AutoTuneWizard motorState={motorState} />
        )}
        {activeTab === 'history' && <RunHistory />}
        {activeTab === 'alarms'  && (
          <AlarmLog motorState={motorState} />
        )}
      </main>

      {/* ── Footer ───────────────────────────── */}
      <footer style={{
        padding: '8px 24px',
        borderTop: '1px solid #1e2535',
        display: 'flex',
        justifyContent: 'space-between',
        fontFamily: 'Share Tech Mono',
        fontSize: 10,
        color: '#1e2535'
      }}>
        <span>PID-SCADA v2.0 · FastAPI + React + SQLite</span>
        <span>Kp={motorState.Kp?.toFixed(3)} · Ki={motorState.Ki?.toFixed(3)} · Kd={motorState.Kd?.toFixed(3)}</span>
      </footer>
    </div>
  )
}
