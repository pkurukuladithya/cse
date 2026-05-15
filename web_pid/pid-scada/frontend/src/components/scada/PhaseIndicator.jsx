import { useScadaStore } from '../../store/useScadaStore'

const PHASES = ['idle', 'ramp', 'tuning', 'stable']

export default function PhaseIndicator() {
  const phase = useScadaStore(s => s.telemetry.phase)
  const running = useScadaStore(s => s.telemetry.running)
  
  const activeIdx = running ? PHASES.indexOf(phase) : -1

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">SYSTEM PHASE</div>
        <div className="text-mono text-accent" style={{ fontSize: 10, textTransform: 'uppercase' }}>
          {running ? phase : 'IDLE'}
        </div>
      </div>
      <div className="panel-body">
        <div className="phase-steps">
          {PHASES.map((p, i) => {
            let className = 'phase-step '
            if (!running && p === 'idle') className += 'active'
            else if (running) {
              if (i < activeIdx) className += 'done'
              else if (i === activeIdx) className += 'active'
            }
            return (
              <div key={p} className={className}>
                {p}
              </div>
            )
          })}
        </div>
        <div className="mt-10 text-muted" style={{ fontSize: 11 }}>
          {!running ? 'System idle — press START' : 
            phase === 'ramp' ? 'Accelerating to setpoint…' :
            phase === 'tuning' ? 'Awaiting settling band…' :
            phase === 'stable' ? 'Target RPM maintained.' : ''}
        </div>
      </div>
    </div>
  )
}
