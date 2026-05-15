/**
 * RunHistory.jsx
 * Displays run data from SQLite with a summary Recharts chart.
 */
import { useState, useEffect } from 'react'
import {
  ResponsiveContainer, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip
} from 'recharts'

export default function RunHistory() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const fetch_ = async () => {
    setLoading(true)
    try {
      const res  = await fetch('/api/history?limit=300')
      const data = await res.json()
      setHistory(data)
    } catch (_) {}
    setLoading(false)
  }

  useEffect(() => { fetch_() }, [])

  // Summary statistics
  const avgRPM    = history.length ? (history.reduce((s, r) => s + r.actual_rpm, 0) / history.length).toFixed(1) : '—'
  const maxRPM    = history.length ? Math.max(...history.map(r => r.actual_rpm)).toFixed(1) : '—'
  const avgPWM    = history.length ? (history.reduce((s, r) => s + r.pwm, 0) / history.length).toFixed(1) : '—'

  const chartData = history.slice(-150).map((r, i) => ({
    i,
    rpm: +r.actual_rpm.toFixed(1),
    setpt: +r.target_rpm.toFixed(1),
    pwm: +r.pwm.toFixed(1),
  }))

  return (
    <div>
      {/* Summary */}
      <div className="history-stats" style={{ marginBottom: 16 }}>
        <div className="stat-box">
          <div className="stat-label">Avg Actual RPM</div>
          <div className="stat-value">{avgRPM}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Peak RPM</div>
          <div className="stat-value">{maxRPM}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Avg PWM</div>
          <div className="stat-value" style={{ color: '#eab308' }}>{avgPWM}%</div>
        </div>
      </div>

      {/* Area Chart */}
      <div className="panel chart-panel" style={{ marginBottom: 16 }}>
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />RPM HISTORY (last 300 samples)</span>
          <button className="btn btn-ghost btn-sm" onClick={fetch_}>↻ Refresh</button>
        </div>
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <defs>
                <linearGradient id="rpmGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#10b981" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="i" hide />
              <YAxis domain={[0, 80]} tick={{ fill: '#475569', fontSize: 11 }} stroke="#1e2535" />
              <Tooltip
                contentStyle={{
                  background: '#0e1117', border: '1px solid #2a3348',
                  borderRadius: 4, fontFamily: 'Share Tech Mono', fontSize: 12
                }}
                labelStyle={{ color: '#475569' }}
                itemStyle={{ color: '#10b981' }}
              />
              <Area
                type="monotone" dataKey="setpt" stroke="#f59e0b"
                strokeDasharray="5 3" strokeWidth={1.5}
                fill="none" isAnimationActive={false}
              />
              <Area
                type="monotone" dataKey="rpm" stroke="#10b981"
                strokeWidth={2} fill="url(#rpmGrad)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Raw data table */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />RAW DATA LOG</span>
          <span style={{ fontFamily: 'Share Tech Mono', fontSize: 11, color: '#475569' }}>
            {history.length} records
          </span>
        </div>
        <div style={{ overflowX: 'auto', maxHeight: 320, overflowY: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>TIME</th>
                <th>TARGET</th>
                <th>ACTUAL</th>
                <th>SMOOTH</th>
                <th>PWM%</th>
                <th>KP</th>
                <th>KI</th>
                <th>KD</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', color: '#334155', padding: 20 }}>
                    {loading ? 'Loading…' : 'No history recorded yet. Start the motor to log data.'}
                  </td>
                </tr>
              )}
              {[...history].reverse().slice(0, 100).map((r, i) => (
                <tr key={r.id || i}>
                  <td>{new Date(r.timestamp * 1000).toLocaleTimeString()}</td>
                  <td style={{ color: '#f59e0b' }}>{r.target_rpm.toFixed(1)}</td>
                  <td style={{ color: '#10b981' }}>{r.actual_rpm.toFixed(1)}</td>
                  <td>{r.smoothed_rpm.toFixed(1)}</td>
                  <td style={{ color: '#eab308' }}>{r.pwm.toFixed(1)}</td>
                  <td>{r.kp.toFixed(3)}</td>
                  <td>{r.ki.toFixed(3)}</td>
                  <td>{r.kd.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
