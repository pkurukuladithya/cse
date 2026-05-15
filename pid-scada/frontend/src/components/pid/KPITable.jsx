import { useScadaStore } from '../../store/useScadaStore.js';
import { formatTime, formatNumber } from '../../utils/formatting.js';

function KPITable() {
  const { riseTime, overshoot, itae, settleTime } = useScadaStore((state) => state.kpis);

  const rows = [
    ['Rise time (10–90%)', formatTime(riseTime)],
    ['Max overshoot', overshoot == null ? '—' : `${formatNumber(overshoot)}%`],
    ['ITAE index', itae == null ? '—' : formatNumber(itae, 0)],
    ['Control effort', settleTime == null ? '—' : formatNumber(settleTime)],
  ];

  return (
    <div className="space-y-3">
      {rows.map(([label, value]) => (
        <div key={label} className="flex items-center justify-between text-sm text-text-secondary">
          <span>{label}</span>
          <span className="text-white text-mono">{value}</span>
        </div>
      ))}
    </div>
  );
}

export default KPITable;
