import { useEffect, useMemo, useState } from 'react';
import { useScadaStore } from '../../store/useScadaStore.js';
import RecipeManager from './RecipeManager.jsx';
import { ChevronRight } from 'lucide-react';

function PIDPanel() {
  const pidParams = useScadaStore((state) => state.pidParams);
  const setPidParams = useScadaStore((state) => state.setPidParams);
  const [localParams, setLocalParams] = useState(pidParams);
  const sendCommand = useScadaStore((state) => state.sendCommand) || (() => {});

  useEffect(() => {
    setLocalParams(pidParams);
  }, [pidParams]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      sendCommand('set_pid', localParams);
      setPidParams(localParams);
    }, 300);
    return () => window.clearTimeout(timer);
  }, [localParams, sendCommand, setPidParams]);

  const controls = [
    { label: 'Kp', key: 'kp', min: 0, max: 10, step: 0.1 },
    { label: 'Ki', key: 'ki', min: 0, max: 10, step: 0.1 },
    { label: 'Kd', key: 'kd', min: 0, max: 2, step: 0.01 },
    { label: 'Setpoint', key: 'setpoint', min: 10, max: 120, step: 1 },
  ];

  return (
    <div className="panel p-5 space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="card-label">PID parameters</p>
          <h2 className="text-xl font-semibold">Live tuning</h2>
        </div>
        <button className="btn-outline btn-green">Apply</button>
      </div>
      <div className="space-y-6">
        {controls.map((control) => (
          <div key={control.key} className="space-y-3">
            <div className="flex items-center justify-between text-sm text-text-secondary">
              <span>{control.label}</span>
              <input
                type="number"
                className="w-20 rounded-xl border border-[rgba(255,255,255,0.08)] bg-bg-surface px-3 py-2 text-right text-white"
                value={localParams[control.key]}
                min={control.min}
                max={control.max}
                step={control.step}
                onChange={(event) => setLocalParams({ ...localParams, [control.key]: parseFloat(event.target.value) || 0 })}
              />
            </div>
            <input
              type="range"
              className="input-range"
              min={control.min}
              max={control.max}
              step={control.step}
              value={localParams[control.key]}
              onChange={(event) => setLocalParams({ ...localParams, [control.key]: parseFloat(event.target.value) || 0 })}
            />
          </div>
        ))}
      </div>
      <div className="mt-4">
        <RecipeManager currentParams={localParams} />
      </div>
    </div>
  );
}

export default PIDPanel;
