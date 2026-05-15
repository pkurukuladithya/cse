import { useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useScadaStore } from '../../store/useScadaStore.js';
import RelayProgress from './RelayProgress.jsx';
import TuneResultCard from './TuneResultCard.jsx';

function AutoTuneWizard() {
  const [step, setStep] = useState(1);
  const [setpoint, setSetpoint] = useState(60);
  const [relayAmp, setRelayAmp] = useState(20);
  const sendCommand = useScadaStore((state) => state.sendCommand) || (() => {});
  const tuneState = useScadaStore((state) => state.tuneState);
  const tuneProgress = useScadaStore((state) => state.tuneProgress);
  const tuneResult = useScadaStore((state) => state.tuneResult);

  const stepContent = useMemo(() => {
    switch (step) {
      case 2:
        return <RelayProgress progress={tuneProgress} />;
      case 3:
        return <TuneResultCard result={tuneResult} />;
      default:
        return (
          <div className="space-y-6">
            <div className="rounded-3xl border border-[rgba(255,255,255,0.08)] bg-bg-surface p-6">
              <div className="mb-4 text-sm text-text-secondary uppercase tracking-[0.24em]">Relay amplitude</div>
              <input type="range" min="5" max="40" value={relayAmp} className="input-range" onChange={(event) => setRelayAmp(Number(event.target.value))} />
              <div className="mt-4 flex items-center justify-between text-sm text-white text-mono">
                <span>{relayAmp}%</span>
                <span>Target: {setpoint} RPM</span>
              </div>
            </div>
            <button className="btn-outline btn-green w-full" onClick={() => { setStep(2); sendCommand('start_autotune', { setpoint, relay_amp: relayAmp }); }}>
              Start relay test
            </button>
          </div>
        );
    }
  }, [relayAmp, sendCommand, setpoint, step, tuneProgress, tuneResult]);

  return (
    <div className="space-y-6">
      <div className="panel p-5">
        <div className="card-label mb-3">Ziegler-Nichols auto-tune wizard</div>
        <div className="grid gap-3 sm:grid-cols-4">
          {['Configure', 'Running', 'Results', 'Apply'].map((label, index) => (
            <div key={label} className={`rounded-2xl p-3 text-center text-xs uppercase tracking-[0.22em] ${step === index + 1 ? 'border border-accent text-accent bg-[rgba(0,200,232,0.08)]' : 'border border-[rgba(255,255,255,0.06)] text-text-secondary'}`}>
              {label}
            </div>
          ))}
        </div>
      </div>
      <motion.div className="panel p-5" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        {stepContent}
      </motion.div>
    </div>
  );
}

export default AutoTuneWizard;
