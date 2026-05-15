/**
 * AlarmLog.jsx
 * Displays alarm history from SQLite via GET /api/alarms.
 */
import { useState, useEffect } from 'react'

function formatTime(ts) {
  return new Date(ts * 1000).toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function formatDate(ts) {
  return new Date(ts * 1000).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}

export default function AlarmLog({ motorState }) {
  const [alarms, setAlarms] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAlarms = async () => {
    setLoading(true)
    try {
      const res  = await fetch('/api/alarms?limit=100')
      const data = await res.json()
      setAlarms(data)
    } catch (_) {}
    setLoading(false)
  }

  useEffect(() => {
    fetchAlarms()
    // Auto-refresh every 5s
    const id = setInterval(fetchAlarms, 5000)
    return () => clearInterval(id)
  }, [])

  // Count by severity
  const counts = alarms.reduce((acc, a) => {
    acc[a.level] = (acc[a.level] || 0) + 1
    return acc
  }, {})

  return (
    <div>
      {/* Summary Cards */}
      <div className="history-stats" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <div className="stat-box">
          <div className="stat-label">Total Events</div>
          <div className="stat-value" style={{ color: '#94a3b8' }}>{alarms.length}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Critical</div>
          <div className="stat-value" style={{ color: '#ef4444' }}>{counts['CRITICAL'] || 0}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Warnings</div>
          <div className="stat-value" style={{ color: '#eab308' }}>{counts['WARNING'] || 0}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Info</div>
          <div className="stat-value" style={{ color: '#3b82f6' }}>{counts['INFO'] || 0}</div>
        </div>
      </div>

      {/* Active alarm badge */}
      {motorState.alarm && (
        <div className="alarm-banner" style={{ marginBottom: 14 }}>
          <span>🚨</span>
          <span style={{ fontWeight: 700 }}>ACTIVE ALARM:</span>
          <span>{motorState.alarm}</span>
        </div>
      )}

      {/* Table */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />EVENT LOG</span>
          <button
            className="btn btn-ghost btn-sm"
            onClick={fetchAlarms}
            disabled={loading}
          >
            {loading ? '↻ Loading…' : '↻ Refresh'}
          </button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>DATE</th>
                <th>TIME</th>
                <th>LEVEL</th>
                <th>MESSAGE</th>
              </tr>
            </thead>
            <tbody>
              {alarms.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', color: '#334155', padding: 24 }}>
                    No alarm events recorded yet.
                  </td>
                </tr>
              )}
              {alarms.map(a => (
                <tr key={a.id}>
                  <td style={{ color: '#334155' }}>{formatDate(a.timestamp)}</td>
                  <td>{formatTime(a.timestamp)}</td>
                  <td>
                    <span className={`alarm-level alarm-${a.level}`}>
                      {a.level}
                    </span>
                  </td>
                  <td style={{ color: '#94a3b8' }}>{a.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
