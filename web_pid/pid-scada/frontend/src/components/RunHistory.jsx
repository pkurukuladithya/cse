import { useState, useEffect } from 'react'

export default function History() {
  const [runs, setRuns] = useState([])

  useEffect(() => {
    fetch('/api/runs?limit=50')
      .then(res => res.json())
      .then(setRuns)
      .catch(console.error)
  }, [])

  const handleExport = () => {
    if (runs.length === 0) return
    const keys = Object.keys(runs[0])
    const csv = [
      keys.join(','),
      ...runs.map(r => keys.map(k => r[k]).join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `scada_runs_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
  }

  return (
    <div className="panel" style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title">RUN HISTORY (SQLITE)</div>
        <button className="btn-ghost btn-sm" onClick={handleExport}>EXPORT CSV</button>
      </div>
      
      <div className="panel-body" style={{ flex: 1, overflowY: 'auto', padding: 0 }}>
        <table>
          <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
            <tr>
              <th>Date/Time</th>
              <th>Source</th>
              <th>SP</th>
              <th>Kp / Ki / Kd</th>
              <th>Rise (s)</th>
              <th>Sett. (s)</th>
              <th>Overshoot</th>
              <th>ITAE</th>
            </tr>
          </thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.id}>
                <td>{new Date(r.ts * 1000).toLocaleString('en-GB')}</td>
                <td><span className="tag">{r.source.toUpperCase()}</span></td>
                <td>{r.setpoint}</td>
                <td>{r.kp} / {r.ki} / {r.kd}</td>
                <td>{r.rise_time ? r.rise_time.toFixed(2) : '—'}</td>
                <td>{r.settle_time ? r.settle_time.toFixed(2) : '—'}</td>
                <td style={{ color: r.overshoot > 10 ? 'var(--red)' : '' }}>
                  {r.overshoot ? `${r.overshoot.toFixed(1)}%` : '—'}
                </td>
                <td>{r.itae ? r.itae.toFixed(2) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
