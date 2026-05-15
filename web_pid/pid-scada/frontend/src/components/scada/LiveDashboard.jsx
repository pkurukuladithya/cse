import { useState } from 'react'
import { useScadaStore } from '../../store/useScadaStore'
import MetricCards from './MetricCards'
import TrendChart from './TrendChart'
import PhaseIndicator from './PhaseIndicator'
import PIDPanel from '../pid/PIDPanel'
import AlarmLog from './AlarmLog'

export default function LiveDashboard() {
  const telemetry = useScadaStore(s => s.telemetry)
  const sendCommand = useScadaStore(s => s.sendCommand)
  
  // Local state for target RPM slider
  const [targetRpm, setTargetRpm] = useState(telemetry.setpoint || 60)

  const handleStart = () => sendCommand('start')
  const handleStop = () => {
    setTargetRpm(0)
    sendCommand('stop')
  }
  
  const handleTargetChange = (val) => {
    setTargetRpm(Number(val))
    sendCommand('set_pid', { setpoint: Number(val) })
  }

  return (
    <div>
      <MetricCards />

      <div className="dashboard-grid">
        <div className="left-col">
          <TrendChart />
          
          <div className="panel" style={{ marginTop: 2 }}>
            <div className="panel-header">
              <div className="panel-title"><span className="dot" />SPEED SETPOINT</div>
              <div className="text-mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                Target: <span className="text-accent">{telemetry.setpoint} RPM</span>
              </div>
            </div>
            <div className="panel-body">
              <div className="slider-row" style={{ margin: 0 }}>
                <div className="slider-label">RPM</div>
                <input
                  type="range" min={0} max={120} step={1}
                  value={targetRpm}
                  onChange={e => handleTargetChange(e.target.value)}
                  disabled={!telemetry.running}
                  style={{ opacity: telemetry.running ? 1 : 0.4 }}
                />
                <div className="slider-input" style={{ width: 70 }}>
                  {targetRpm} <span style={{ fontSize: 9, color: 'var(--text-muted)' }}>RPM</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="right-col">
          <PIDPanel />
          
          <div className="panel">
            <div className="panel-header">
              <div className="panel-title">CONTROL ACTIONS</div>
            </div>
            <div className="panel-body">
              <div className="btn-row" style={{ flexDirection: 'column', gap: 10 }}>
                <div className="flex gap-10">
                  <button 
                    className="btn btn-start" style={{ flex: 1 }}
                    onClick={handleStart}
                    disabled={telemetry.running}
                  >
                    ▶ START
                  </button>
                  <button 
                    className="btn btn-stop" style={{ flex: 1 }}
                    onClick={handleStop}
                  >
                    ■ E-STOP
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <PhaseIndicator />
        </div>
      </div>
    </div>
  )
}
