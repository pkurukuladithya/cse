/**
 * MetricCards.jsx — 4 HUD cards: Smoothed RPM, PWM, Overshoot, SSE, Settling Time
 */
export default function MetricCards({ state }) {
  const { smoothed_rpm, pwm, overshoot, sse, settling_time, target_rpm } = state

  const cards = [
    {
      label:  'Actual Speed',
      value:  `${smoothed_rpm.toFixed(1)}`,
      unit:   'RPM',
      sub:    `setpoint: ${target_rpm.toFixed(1)} RPM`,
      color:  'green',
    },
    {
      label:  'PWM Output',
      value:  `${pwm.toFixed(1)}`,
      unit:   '%',
      sub:    'duty cycle',
      color:  'yellow',
    },
    {
      label:  'Max Overshoot',
      value:  `${overshoot.toFixed(1)}`,
      unit:   '%',
      sub:    'above setpoint',
      color:  'red',
    },
    {
      label:  'Steady-State Err',
      value:  `${sse.toFixed(1)}`,
      unit:   '%',
      sub:    'SSE',
      color:  'blue',
    },
  ]

  return (
    <div className="metrics-grid">
      {cards.map(c => (
        <div key={c.label} className={`metric-card ${c.color}`}>
          <div className="metric-label">{c.label}</div>
          <div className={`metric-value ${c.color}`}>
            {c.value}
            <span style={{ fontSize: 14, marginLeft: 4, opacity: 0.7 }}>{c.unit}</span>
          </div>
          <div className="metric-sub">{c.sub}</div>
        </div>
      ))}
    </div>
  )
}
