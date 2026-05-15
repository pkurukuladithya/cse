import { useScadaStore } from '../../store/useScadaStore'

export default function RelayProgress() {
  const { elapsed, total, peaks_found, progress } = useScadaStore(s => s.tuneProgress)

  return (
    <div>
      <div className="text-accent text-mono text-center" style={{ fontSize: 24, margin: '20px 0' }}>
        ANALYSING...
      </div>
      
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <div className="kpi-grid mt-10">
        <div className="kpi-item">
          <span className="kpi-label">Peaks Detected</span>
          <span className="kpi-value">{peaks_found} / 4</span>
        </div>
        <div className="kpi-item">
          <span className="kpi-label">Elapsed Time</span>
          <span className="kpi-value">{elapsed.toFixed(1)}s</span>
        </div>
      </div>
      
      <div className="text-muted mt-10" style={{ fontSize: 11, textAlign: 'center' }}>
        Please wait. Motor is intentionally oscillating.
      </div>
    </div>
  )
}
