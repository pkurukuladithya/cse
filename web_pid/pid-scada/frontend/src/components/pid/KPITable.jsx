import { useScadaStore } from '../../store/useScadaStore'

export default function KPITable() {
  const telemetry = useScadaStore(s => s.telemetry)
  
  const metrics = [
    { label: 'Rise Time', value: telemetry.rise_time, unit: 's' },
    { label: 'Overshoot', value: telemetry.overshoot, unit: '%' },
    { label: 'Settle Time', value: telemetry.settle_time, unit: 's' },
    { label: 'ITAE', value: telemetry.itae, unit: '' },
    { label: 'Mean Effort', value: telemetry.pwm_mean, unit: '%' }
  ]

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">PERFORMANCE KPIs</div>
      </div>
      <div className="panel-body">
        <div className="kpi-grid">
          {metrics.map(m => (
            <div key={m.label} className="kpi-item">
              <span className="kpi-label">{m.label}</span>
              <span className="kpi-value">
                {m.value === null ? '—' : `${Number(m.value).toFixed(2)}${m.unit}`}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-10 text-muted" style={{ fontSize: 10 }}>
          KPIs reset upon setpoint change.
        </div>
      </div>
    </div>
  )
}
