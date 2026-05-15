function RelayProgress({ progress }) {
  return (
    <div className="space-y-5">
      <div className="rounded-3xl border border-[rgba(255,255,255,0.08)] bg-bg-surface p-6 text-center">
        <p className="text-sm text-text-secondary uppercase tracking-[0.24em]">Oscillation in progress</p>
        <div className="mt-5 text-3xl font-semibold text-accent">{progress?.elapsed ?? 0}s</div>
        <p className="mt-2 text-sm text-text-secondary">Peaks found: {progress?.peaks_found ?? 0}</p>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-bg-panel">
        <div className="h-full bg-accent" style={{ width: `${((progress?.elapsed ?? 0) / (progress?.total ?? 15)) * 100}%` }} />
      </div>
      <div className="text-sm text-text-secondary">Status: {progress?.status ?? 'warming up'}</div>
    </div>
  );
}

export default RelayProgress;
