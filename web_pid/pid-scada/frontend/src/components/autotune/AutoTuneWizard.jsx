import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useScadaStore } from '../../store/useScadaStore'
import RelayProgress from './RelayProgress'
import TuneResultCard from './TuneResultCard'
import TrendChart from '../scada/TrendChart'

const STEPS = ['Configure', 'Running', 'Results', 'Apply']

export default function AutoTuneWizard() {
  const telemetry = useScadaStore(s => s.telemetry)
  const sendCommand = useScadaStore(s => s.sendCommand)
  const tuneState = useScadaStore(s => s.tuneState)
  const tuneResult = useScadaStore(s => s.tuneResult)
  const resetTuneState = useScadaStore(s => s.resetTuneState)

  const [step, setStep] = useState(0)
  const [target, setTarget] = useState(60)
  const [amp, setAmp] = useState(20)

  // Auto-advance logic
  if (tuneState === 'running' && step === 0) setStep(1)
  if (tuneState === 'complete' && step === 1) setStep(2)

  const handleStart = () => {
    sendCommand('start_autotune', { setpoint: target, relay_amp: amp })
  }

  const handleApply = () => {
    if (tuneResult) {
      sendCommand('set_pid', { 
        kp: tuneResult.kp, 
        ki: tuneResult.ki, 
        kd: tuneResult.kd,
        setpoint: target 
      })
      sendCommand('start')
      setStep(3) // Advance to confirm
    }
  }

  const handleReset = () => {
    resetTuneState()
    setStep(0)
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: 16 }}>
      
      {/* LEFT: Chart (always visible to see oscillations) */}
      <div style={{ height: 400 }}>
        <TrendChart />
      </div>

      {/* RIGHT: Wizard */}
      <div className="panel" style={{ height: 400, display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header">
          <div className="panel-title">ZIEGLER-NICHOLS AUTO-TUNE</div>
        </div>
        
        <div className="panel-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          
          {/* Step Indicator */}
          <div className="wizard-steps">
            {STEPS.map((s, i) => (
              <div key={s} className={`wizard-step ${i === step ? 'active' : i < step ? 'done' : ''}`}>
                {s}
              </div>
            ))}
          </div>

          <div style={{ flex: 1, position: 'relative' }}>
            <AnimatePresence mode="wait">
              
              {/* STEP 0: Configure */}
              {step === 0 && (
                <motion.div
                  key="step0"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <div className="text-muted mb-12">
                    System will switch to relay (bang-bang) control to induce sustained oscillations.
                  </div>
                  
                  <div className="slider-row">
                    <div className="slider-label">TEST RPM</div>
                    <input type="range" min={20} max={100} value={target} onChange={e => setTarget(Number(e.target.value))} />
                    <div className="slider-input">{target}</div>
                  </div>
                  
                  <div className="slider-row">
                    <div className="slider-label">RELAY ±%</div>
                    <input type="range" min={5} max={50} value={amp} onChange={e => setAmp(Number(e.target.value))} />
                    <div className="slider-input">{amp}</div>
                  </div>
                  
                  <button className="btn btn-start" style={{ width: '100%', marginTop: 20 }} onClick={handleStart}>
                    START RELAY TEST
                  </button>
                </motion.div>
              )}

              {/* STEP 1: Running */}
              {step === 1 && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <RelayProgress />
                  {tuneState === 'error' && (
                    <div className="mt-10">
                      <div className="alarm-banner">Auto-tune failed. See alarm log.</div>
                      <button className="btn btn-ghost" style={{ width: '100%' }} onClick={handleReset}>RETRY</button>
                    </div>
                  )}
                </motion.div>
              )}

              {/* STEP 2: Results */}
              {step === 2 && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <TuneResultCard result={tuneResult} oldParams={{ kp: telemetry.kp, ki: telemetry.ki, kd: telemetry.kd }} />
                  <div className="flex gap-10 mt-10">
                    <button className="btn btn-ghost" style={{ flex: 1 }} onClick={handleReset}>DISCARD</button>
                    <button className="btn btn-accent" style={{ flex: 1 }} onClick={handleApply}>APPLY GAINS</button>
                  </div>
                </motion.div>
              )}

              {/* STEP 3: Applied */}
              {step === 3 && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  style={{ textAlign: 'center', paddingTop: 40 }}
                >
                  <div style={{ fontSize: 40, color: 'var(--green)', marginBottom: 10 }}>✓</div>
                  <div className="text-secondary" style={{ fontSize: 16, marginBottom: 20 }}>
                    Parameters applied.<br/>System running with new gains.
                  </div>
                  <button className="btn btn-ghost" onClick={handleReset}>FINISH</button>
                </motion.div>
              )}
              
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
