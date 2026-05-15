/**
 * LiveDashboard.jsx - FIXED
 * - Target RPM slider lives HERE (not in PIDPanel) so it's always visible
 * - Slider uses local state so WebSocket doesn't fight it
 * - Start/Stop buttons work cleanly
 */
import { useState, useEffect } from 'react'
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts'
import MetricCards from './MetricCards'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#0e1117', border: '1px solid #2a3348',
      borderRadius: 4, padding: '8px 12px',
      fontFamily: 'Share Tech Mono, monospace', fontSize: 12
    }}>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, marginBottom: 2 }}>
          {p.name}: {Number(p.value).toFixed(2)} RPM
        </div>
      ))}
    </div>
  )
}

export default function LiveDashboard({ motorState, trendData, sendUpdate }) {
  const { running, alarm, settling_time } = motorState

  // Target RPM lives in LOCAL state — not overwritten by WebSocket
  const [targetRpm, setTargetRpm] = useState(motorState.target_rpm || 0)

  const handleTargetChange = (v) => {
    setTargetRpm(+v)
    sendUpdate({ target_rpm: +v })
  }

  const handleStart = () => {
    sendUpdate({ running: true })
  }

  const handleStop = () => {
    setTargetRpm(0)
    sendUpdate({ running: false, target_rpm: 0 })
  }

  return (
    <div>
      {/* Alarm Banner */}
      {alarm && (
        <div className="alarm-banner">
          <span>⚠</span>
          <span>{alarm}</span>
        </div>
      )}

      {/* HUD Cards */}
      <MetricCards state={motorState} />

      {/* Trend Chart */}
      <div className="panel chart-panel" style={{ marginBottom: 16 }}>
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />LIVE TREND — RPM vs TIME</span>
          <span style={{ fontFamily: 'Share Tech Mono', fontSize: 11, color: '#475569' }}>
            SETTLING TIME: <span style={{ color: '#10b981' }}>{settling_time.toFixed(2)}s</span>
          </span>
        </div>
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="t" hide />
              <YAxis domain={[0, 80]} tick={{ fill: '#475569', fontSize: 11 }} stroke="#1e2535" />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontFamily: 'Share Tech Mono', fontSize: 11, color: '#64748b', paddingTop: 8 }} />
              <Line type="monotone" dataKey="setpt"  name="Setpoint"
                stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 4"
                dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="smooth" name="Actual (filtered)"
                stroke="#10b981" strokeWidth={2.5}
                dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="raw"    name="Raw sensor"
                stroke="#334155" strokeWidth={1}
                dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Target RPM Slider — RIGHT HERE on the dashboard */}
      <div className="panel" style={{ marginBottom: 12 }}>
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />SPEED SETPOINT</span>
          <span style={{ fontFamily: 'Share Tech Mono', fontSize: 11, color: '#475569' }}>
            Backend target: <span style={{ color: '#f59e0b' }}>{motorState.target_rpm?.toFixed(1)} RPM</span>
          </span>
        </div>
        <div className="panel-body">
          <div className="slider-row" style={{ margin: 0 }}>
            <span className="slider-label">Target RPM</span>
            <input
              type="range" min={0} max={60} step={1}
              value={targetRpm}
              onChange={e => handleTargetChange(e.target.value)}
              disabled={!running}
              style={{ opacity: running ? 1 : 0.4 }}
            />
            <span className="slider-display" style={{ minWidth: 70 }}>
              {targetRpm} <span style={{ fontSize: 9, opacity: 0.6 }}>RPM</span>
            </span>
          </div>
          {!running && (
            <div style={{ fontFamily: 'Share Tech Mono', fontSize: 11, color: '#475569', marginTop: 8 }}>
              ↑ Press START to enable speed control
            </div>
          )}
        </div>
      </div>

      {/* Start / Stop */}
      <div className="btn-row">
        <button
          className="btn btn-start"
          onClick={handleStart}
          disabled={running}
          style={{ opacity: running ? 0.5 : 1 }}
        >
          ▶ SYSTEM START
        </button>
        <button className="btn btn-stop" onClick={handleStop}>
          ⏹ EMERGENCY STOP
        </button>
      </div>
    </div>
  )
}
