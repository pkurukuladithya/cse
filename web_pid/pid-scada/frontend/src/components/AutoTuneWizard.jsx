/**
 * AutoTuneWizard.jsx
 * Step-by-step Z-N relay auto-tuner UI.
 */
import { useState, useEffect, useRef } from 'react'

const STEPS = ['Configure', 'Running Test', 'Results', 'Apply']

export default function AutoTuneWizard({ motorState }) {
  const [step, setStep]           = useState(0)
  const [setpoint, setSetpoint]   = useState(40)
  const [atState, setAtState]     = useState(null)
  const [polling, setPolling]     = useState(false)
  const pollRef = useRef(null)

  // Poll backend state while active
  useEffect(() => {
    if (polling) {
      pollRef.current = setInterval(async () => {
        const res  = await fetch('/api/state')
        const data = await res.json()
        setAtState(data.autotune)

        if (data.autotune.status === 'SUCCESS') {
          setStep(2)
          setPolling(false)
        } else if (data.autotune.status === 'FAILED') {
          setStep(0)
          setPolling(false)
          alert('Auto-tune failed: ' + (data.autotune.log?.slice(-1)[0] || 'Unknown error'))
        }
      }, 500)
    }
    return () => clearInterval(pollRef.current)
  }, [polling])

  const startTune = async () => {
    const res  = await fetch('/api/autotune/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ setpoint_rpm: setpoint }),
    })
    const data = await res.json()
    if (data.error) { alert(data.error); return }
    setStep(1)
    setPolling(true)
  }

  const applyResults = async () => {
    await fetch('/api/autotune/apply', { method: 'POST' })
    setStep(3)
  }

  const reset = () => { setStep(0); setAtState(null) }

  const at = atState || motorState.autotune

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="panel-title"><span className="dot" />AUTO-TUNE WIZARD — Z-N RELAY METHOD</span>
        <span className="tag">EXPERIMENTAL</span>
      </div>
      <div className="panel-body">

        {/* Step Indicators */}
        <div className="wizard-steps">
          {STEPS.map((s, i) => (
            <div
              key={s}
              className={`wizard-step ${i === step ? 'active' : i < step ? 'done' : ''}`}
            >
              {i < step ? '✓ ' : `${i+1}. `}{s}
            </div>
          ))}
        </div>

        {/* ── Step 0: Configure ───────────────── */}
        {step === 0 && (
          <div>
            <p style={{ color: '#64748b', fontSize: 13, marginBottom: 16, lineHeight: 1.6 }}>
              The auto-tuner will run a relay test on your motor. It switches the motor
              ON and OFF rapidly around the setpoint RPM, measures the natural oscillation
              frequency (Pu), and calculates the best Kp, Ki, Kd values using the
              Ziegler-Nichols method.
            </p>

            <div className="slider-row" style={{ maxWidth: 420 }}>
              <span className="slider-label">Test Setpoint</span>
              <input
                type="range" min={10} max={55} step={5}
                value={setpoint} onChange={e => setSetpoint(+e.target.value)}
              />
              <span className="slider-display">{setpoint} <span style={{ fontSize: 9, opacity: 0.6 }}>RPM</span></span>
            </div>

            <div style={{
              background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.2)',
              borderRadius: 5, padding: '10px 14px', marginBottom: 16,
              fontFamily: 'Share Tech Mono', fontSize: 12, color: '#b45309'
            }}>
              ⚠ Ensure the motor can spin freely at {setpoint} RPM before starting.
              The relay test will take up to 60 seconds.
            </div>

            <button className="btn btn-amber" style={{ maxWidth: 240 }} onClick={startTune}>
              START RELAY TEST
            </button>
          </div>
        )}

        {/* ── Step 1: Running ─────────────────── */}
        {step === 1 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#64748b', fontSize: 13 }}>
                Collecting oscillation data at {setpoint} RPM…
              </span>
              <span style={{ fontFamily: 'Share Tech Mono', fontSize: 12, color: '#f59e0b' }}>
                {at?.progress ?? 0}%
              </span>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${at?.progress ?? 0}%` }} />
            </div>

            <div className="log-box" style={{ marginTop: 12 }}>
              {(at?.log ?? []).map((entry, i) => (
                <div key={i} className={`log-entry ${entry.includes('SUCCESS') ? 'success' : ''}`}>
                  {entry}
                </div>
              ))}
              {!at?.log?.length && (
                <div className="log-entry">Waiting for relay oscillations…</div>
              )}
            </div>

            <div style={{ marginTop: 12, fontFamily: 'Share Tech Mono', fontSize: 11, color: '#334155' }}>
              Live: {motorState.smoothed_rpm?.toFixed(1)} RPM
            </div>
          </div>
        )}

        {/* ── Step 2: Results ─────────────────── */}
        {step === 2 && at?.result && (
          <div>
            <div style={{ color: '#10b981', fontFamily: 'Share Tech Mono', fontSize: 13, marginBottom: 14 }}>
              ✓ Tuning complete — Ziegler-Nichols parameters calculated
            </div>

            <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
              <div className="result-box" style={{ flex: 1 }}>
                <div className="rb-label">Ku (Ultimate Gain)</div>
                <div className="rb-value">{at.result.Ku}</div>
              </div>
              <div className="result-box" style={{ flex: 1 }}>
                <div className="rb-label">Pu (Period)</div>
                <div className="rb-value">{at.result.Pu}s</div>
              </div>
            </div>

            <div className="result-grid">
              <div className="result-box">
                <div className="rb-label">Kp</div>
                <div className="rb-value">{at.result.Kp}</div>
              </div>
              <div className="result-box">
                <div className="rb-label">Ki</div>
                <div className="rb-value">{at.result.Ki}</div>
              </div>
              <div className="result-box">
                <div className="rb-label">Kd</div>
                <div className="rb-value">{at.result.Kd}</div>
              </div>
            </div>

            <div className="btn-row" style={{ marginTop: 16 }}>
              <button className="btn btn-start" onClick={applyResults}>
                ✓ APPLY TO SYSTEM
              </button>
              <button className="btn btn-ghost" onClick={reset}>
                DISCARD
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Done ────────────────────── */}
        {step === 3 && (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
            <div style={{ color: '#10b981', fontFamily: 'Share Tech Mono', fontSize: 16, marginBottom: 8 }}>
              PID parameters applied to live system
            </div>
            <div style={{ color: '#475569', fontSize: 13, marginBottom: 20 }}>
              Switch to the PID Tuning tab to fine-tune if needed.
            </div>
            <button className="btn btn-ghost btn-sm" onClick={reset}>
              Run Another Test
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
