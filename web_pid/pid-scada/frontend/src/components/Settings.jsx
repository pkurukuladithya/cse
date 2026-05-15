import { useState, useEffect } from 'react'

export default function Settings() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(setStatus)
      .catch(console.error)
  }, [])

  return (
    <div className="panel" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="panel-header">
        <div className="panel-title">SYSTEM SETTINGS &amp; INFO</div>
      </div>
      <div className="panel-body">
        
        <div className="kpi-grid mb-12">
          <div className="kpi-item">
            <span className="kpi-label">Node Status</span>
            <span className="kpi-value">
              {status ? (status.mock_mode ? 'MOCK DRIVER' : 'HARDWARE ACTIVE') : '...'}
            </span>
          </div>
          <div className="kpi-item">
            <span className="kpi-label">Connected Clients</span>
            <span className="kpi-value">{status?.connected_clients || 0}</span>
          </div>
          <div className="kpi-item">
            <span className="kpi-label">Uptime</span>
            <span className="kpi-value">
              {status ? (status.uptime / 3600).toFixed(2) + ' hr' : '...'}
            </span>
          </div>
          <div className="kpi-item">
            <span className="kpi-label">System Version</span>
            <span className="kpi-value">{status?.version || '...'}</span>
          </div>
        </div>

        <div className="section-sep"></div>

        <div className="text-secondary" style={{ fontSize: 13, marginBottom: 8, fontFamily: 'var(--font-head)', fontWeight: 700, textTransform: 'uppercase' }}>
          Hardware Configuration
        </div>
        <table style={{ marginBottom: 20 }}>
          <tbody>
            <tr><td>Motor Driver</td><td>TB6612FNG Dual H-Bridge</td></tr>
            <tr><td>PWM Pin</td><td>GPIO 12 (1 kHz)</td></tr>
            <tr><td>Direction Pins</td><td>GPIO 23 (AIN1), GPIO 24 (AIN2)</td></tr>
            <tr><td>Encoder Pins</td><td>GPIO 17 (Ch A), GPIO 27 (Ch B)</td></tr>
            <tr><td>Gear Ratio</td><td>30:1 (PPR 7)</td></tr>
          </tbody>
        </table>

        <div className="section-sep"></div>

        <div className="text-secondary" style={{ fontSize: 13, marginBottom: 8, fontFamily: 'var(--font-head)', fontWeight: 700, textTransform: 'uppercase' }}>
          Machine Learning Control (Experimental)
        </div>
        <div className="alarm-banner" style={{ background: 'rgba(245,166,35,0.05)', borderColor: 'rgba(245,166,35,0.3)', color: 'var(--amber)', animation: 'none' }}>
          ML-based Bayesian Auto-Tuning is currently disabled. Model weights must be downloaded to the Raspberry Pi before enabling.
        </div>

      </div>
    </div>
  )
}
