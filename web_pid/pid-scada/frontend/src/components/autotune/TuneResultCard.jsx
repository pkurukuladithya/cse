export default function TuneResultCard({ result, oldParams }) {
  if (!result) return null

  const confColor = result.confidence > 0.8 ? 'var(--green)' : result.confidence > 0.5 ? 'var(--amber)' : 'var(--red)'

  return (
    <div>
      <div className="flex justify-between align-center mb-8">
        <div className="text-secondary" style={{ fontSize: 11, textTransform: 'uppercase' }}>Suggested Parameters</div>
        <div className="tag" style={{ color: confColor, borderColor: confColor }}>
          CONFIDENCE: {(result.confidence * 100).toFixed(0)}%
        </div>
      </div>
      
      <div className="result-grid">
        <div className="result-box">
          <div className="rb-label">Kp</div>
          <div className="rb-old">{oldParams.kp.toFixed(2)}</div>
          <div className="rb-new">{result.kp.toFixed(2)}</div>
        </div>
        <div className="result-box">
          <div className="rb-label">Ki</div>
          <div className="rb-old">{oldParams.ki.toFixed(2)}</div>
          <div className="rb-new">{result.ki.toFixed(2)}</div>
        </div>
        <div className="result-box">
          <div className="rb-label">Kd</div>
          <div className="rb-old">{oldParams.kd.toFixed(2)}</div>
          <div className="rb-new">{result.kd.toFixed(2)}</div>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-item">
          <span className="kpi-label">Ult. Gain (Ku)</span>
          <span className="kpi-value">{result.ku.toFixed(2)}</span>
        </div>
        <div className="kpi-item">
          <span className="kpi-label">Ult. Period (Tu)</span>
          <span className="kpi-value">{result.tu.toFixed(2)}s</span>
        </div>
      </div>
    </div>
  )
}
