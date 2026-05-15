import { useState, useEffect } from 'react'
import { useScadaStore } from '../../store/useScadaStore'
import RecipeManager from './RecipeManager'

export default function PIDPanel() {
  const telemetry = useScadaStore(s => s.telemetry)
  const sendCommand = useScadaStore(s => s.sendCommand)
  
  // Local state for sliders (allows smooth dragging before sending to backend)
  const [params, setParams] = useState({ kp: 1.5, ki: 1.5, kd: 0.01 })
  const [synced, setSynced] = useState(true)

  // Sync from backend when changed externally (e.g. recipe load)
  useEffect(() => {
    setParams({ kp: telemetry.kp, ki: telemetry.ki, kd: telemetry.kd })
    setSynced(true)
  }, [telemetry.kp, telemetry.ki, telemetry.kd])

  const handleChange = (key, val) => {
    const newVal = Number(val)
    setParams(p => ({ ...p, [key]: newVal }))
    setSynced(false)
  }

  // Debounced send to backend
  useEffect(() => {
    if (synced) return
    const timer = setTimeout(() => {
      sendCommand('set_pid', params)
      setSynced(true)
    }, 300)
    return () => clearTimeout(timer)
  }, [params, synced, sendCommand])

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">PID PARAMETERS</div>
        <div className="text-mono" style={{ fontSize: 10, color: synced ? 'var(--green)' : 'var(--amber)' }}>
          {synced ? 'SYNCED' : 'UPDATING...'}
        </div>
      </div>
      <div className="panel-body">
        
        <div className="slider-row">
          <div className="slider-label">Kp</div>
          <input type="range" min={0} max={10} step={0.1} value={params.kp} onChange={e => handleChange('kp', e.target.value)} />
          <input type="number" className="slider-input" value={params.kp} onChange={e => handleChange('kp', e.target.value)} step={0.1} />
        </div>
        
        <div className="slider-row">
          <div className="slider-label">Ki</div>
          <input type="range" min={0} max={10} step={0.1} value={params.ki} onChange={e => handleChange('ki', e.target.value)} />
          <input type="number" className="slider-input" value={params.ki} onChange={e => handleChange('ki', e.target.value)} step={0.1} />
        </div>
        
        <div className="slider-row">
          <div className="slider-label">Kd</div>
          <input type="range" min={0} max={2} step={0.01} value={params.kd} onChange={e => handleChange('kd', e.target.value)} />
          <input type="number" className="slider-input" value={params.kd} onChange={e => handleChange('kd', e.target.value)} step={0.01} />
        </div>

        <RecipeManager currentParams={params} />
      </div>
    </div>
  )
}
