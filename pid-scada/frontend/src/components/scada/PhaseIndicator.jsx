function PhaseIndicator({ phase }) {
  const steps = [
    { key: 'idle', label: 'Init' },
    { key: 'ramp', label: 'Ramp' },
    { key: 'tuning', label: 'Tune' },
    { key: 'stable', label: 'Stable' },
  ];

  return (
    <div className="panel p-5">
      <div className="card-label">System phase</div>
      <div className="mt-4 grid grid-cols-4 gap-3">
        {steps.map((step) => {
          const active = step.key === phase;
          const done = steps.findIndex((item) => item.key === item.key) < steps.findIndex((item) => item.key === phase);
          return (
            <div key={step.key} className={`rounded-xl border p-3 text-center text-xs uppercase tracking-[0.24em] ${active ? 'border-accent text-accent bg-[rgba(0,200,232,0.08)]' : 'border-[rgba(255,255,255,0.06)] text-text-secondary'}`}>
              {step.label}
            </div>
          );
        })}
      </div>
      <p className="mt-4 text-sm text-text-secondary">Current phase: <span className="text-white">{phase}</span></p>
    </div>
  );
}

export default PhaseIndicator;
