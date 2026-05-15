function TuneResultCard({ result }) {
  const rows = [
    ['Kp', result?.kp ?? '—'],
    ['Ki', result?.ki ?? '—'],
    ['Kd', result?.kd ?? '—'],
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-[rgba(255,255,255,0.08)] bg-bg-surface p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="card-label">Auto-tune result</p>
            <h2 className="text-xl font-semibold">Suggested PID gains</h2>
          </div>
          <div className="rounded-2xl bg-[rgba(0,229,160,0.12)] px-4 py-2 text-sm text-green">Confidence {result?.confidence_score ?? '—'}</div>
        </div>
        <div className="mt-6 grid gap-3 text-sm text-text-secondary">
          {rows.map(([label, value]) => (
            <div key={label} className="grid grid-cols-[1fr_auto] gap-4 rounded-2xl bg-bg-panel p-4">
              <span>{label}</span>
              <span className="text-white text-mono">{value}</span>
            </div>
          ))}
        </div>
      </div>
      <button className="btn-outline btn-green w-full">Apply parameters</button>
    </div>
  );
}

export default TuneResultCard;
