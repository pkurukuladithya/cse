import { formatNumber } from '../../utils/formatting.js';

const cards = [
  { key: 'rpm', label: 'Actual RPM', unit: 'rpm', accent: 'text-accent' },
  { key: 'pwm', label: 'PWM Duty', unit: '%', accent: 'text-amber' },
  { key: 'error', label: 'Steady-State Error', unit: '%', accent: 'text-green' },
  { key: 'setpoint', label: 'Setpoint', unit: 'rpm', accent: 'text-purple' },
];

function MetricCards({ telemetry }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const value = telemetry[card.key] ?? 0;
        const textColor = card.key === 'error' && value > 8 ? 'text-red' : card.accent;
        return (
          <div key={card.key} className="panel p-5">
            <div className="card-label">{card.label}</div>
            <div className={`mt-4 text-4xl font-semibold text-white ${textColor} text-mono`}>
              {formatNumber(value)}{card.unit}
            </div>
            <div className="mt-4 h-2 rounded-full bg-bg-surface overflow-hidden">
              <div className="h-full rounded-full bg-accent" style={{ width: `${Math.min(100, Math.abs(value))}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default MetricCards;
