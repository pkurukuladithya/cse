import { useScadaStore } from '../../store/useScadaStore'

function Card({ label, value, unit, colorClass, max }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100))
  
  return (
    <div className={`metric-card ${colorClass}`}>
      <div className="metric-label">{label}</div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span className={`metric-value ${colorClass}`}>
          {typeof value === 'number' ? value.toFixed(1) : value}
        </span>
        <span className="metric-unit">{unit}</span>
      </div>
      <div className="metric-bar">
        <div className={`metric-bar-fill`} style={{ width: `${pct}%`, background: `var(--${colorClass})` }} />
      </div>
    </div>
  )
}

export default function MetricCards() {
  const telemetry = useScadaStore(s => s.telemetry)

  const { rpm, pwm, error, setpoint, settle_time } = telemetry

  // Determine colors based on thresholds
  const rpmColor = rpm > 110 ? 'red' : rpm > setpoint * 1.1 ? 'amber' : 'cyan'
  const errorColor = Math.abs(error) < (setpoint * 0.02) ? 'green' : 'amber'
  const settleDisp = settle_time === null ? '—' : settle_time.toFixed(2)

  return (
    <div className="metrics-grid">
      <Card label="Actual RPM" value={rpm} unit="rpm" colorClass={rpmColor} max={120} />
      <Card label="PWM Duty" value={pwm} unit="%" colorClass="amber" max={100} />
      <Card label="Steady-State Err" value={Math.abs(error)} unit={error === 0 ? '' : 'rpm'} colorClass={errorColor} max={20} />
      <Card label="Setpoint" value={setpoint} unit="rpm" colorClass="purple" max={120} />
    </div>
  )
}
