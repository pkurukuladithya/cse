import { useMemo } from 'react';
import { useScadaStore } from '../../store/useScadaStore.js';
import TrendChart from './TrendChart.jsx';
import MetricCards from './MetricCards.jsx';
import PhaseIndicator from './PhaseIndicator.jsx';
import AlarmLog from './AlarmLog.jsx';
import PIDPanel from '../pid/PIDPanel.jsx';
import KPITable from '../pid/KPITable.jsx';

function LiveDashboard() {
  const telemetry = useScadaStore((state) => state.telemetry);
  const trendBuffer = useScadaStore((state) => state.trendBuffer);
  const phase = useScadaStore((state) => state.phase);

  const trendData = useMemo(
    () => trendBuffer.map((item) => ({ ts: item.ts, rpm: item.rpm })),
    [trendBuffer]
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
      <div className="space-y-6">
        <MetricCards telemetry={{ ...telemetry, setpoint: telemetry.setpoint }} />
        <TrendChart data={trendData} setpoint={telemetry.setpoint} />
        <div className="grid gap-6 md:grid-cols-2">
          <PhaseIndicator phase={phase} />
          <div className="panel p-5">
            <div className="card-label">Performance KPIs</div>
            <div className="mt-4 grid gap-3">
              <KPITable />
            </div>
          </div>
        </div>
      </div>
      <div className="space-y-6">
        <PIDPanel />
        <AlarmLog />
      </div>
    </div>
  );
}

export default LiveDashboard;
