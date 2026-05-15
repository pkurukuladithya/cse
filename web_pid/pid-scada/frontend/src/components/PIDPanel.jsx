/**
 * PIDPanel.jsx
 * Kp/Ki/Kd + Target RPM sliders with live send + recipe save/load.
 */
import { useState, useEffect } from 'react'

export default function PIDPanel({ motorState, sendUpdate }) {
  const [local, setLocal] = useState({
    target_rpm: motorState.target_rpm,
    Kp: motorState.Kp,
    Ki: motorState.Ki,
    Kd: motorState.Kd,
  })
  const [recipes, setRecipes]         = useState([])
  const [recipeName, setRecipeName]   = useState('')
  const [saving, setSaving]           = useState(false)

  // Sync if auto-tuner applies new values
  useEffect(() => {
    setLocal(l => ({
      ...l,
      Kp: motorState.Kp,
      Ki: motorState.Ki,
      Kd: motorState.Kd,
    }))
  }, [motorState.Kp, motorState.Ki, motorState.Kd])

  // Load recipes on mount
  useEffect(() => { fetchRecipes() }, [])

  const fetchRecipes = async () => {
    const res  = await fetch('/api/recipes')
    const data = await res.json()
    setRecipes(data)
  }

  const handleSlider = (key, val) => {
    const v = parseFloat(val)
    setLocal(l => ({ ...l, [key]: v }))
    sendUpdate({ [key]: v })
  }

  const sliders = [
    { key: 'target_rpm', label: 'Target RPM',       min: 0,   max: 60,  step: 1,    unit: 'RPM' },
    { key: 'Kp',         label: 'Proportional (Kp)', min: 0,   max: 10,  step: 0.05, unit: '' },
    { key: 'Ki',         label: 'Integral (Ki)',      min: 0,   max: 5,   step: 0.05, unit: '' },
    { key: 'Kd',         label: 'Derivative (Kd)',    min: 0,   max: 1,   step: 0.01, unit: '' },
  ]

  const saveRecipe = async () => {
    if (!recipeName.trim()) return
    setSaving(true)
    await fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: recipeName, kp: local.Kp, ki: local.Ki, kd: local.Kd }),
    })
    setRecipeName('')
    await fetchRecipes()
    setSaving(false)
  }

  const loadRecipe = (r) => {
    const patch = { Kp: r.kp, Ki: r.ki, Kd: r.kd }
    setLocal(l => ({ ...l, ...patch }))
    sendUpdate(patch)
  }

  const deleteRecipe = async (id) => {
    await fetch(`/api/recipes/${id}`, { method: 'DELETE' })
    fetchRecipes()
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

      {/* ── Left: Sliders ─────────────────── */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />PID PARAMETERS</span>
          <span className="tag">LIVE</span>
        </div>
        <div className="panel-body">
          {sliders.map(s => (
            <div key={s.key} className="slider-row">
              <span className="slider-label">{s.label}</span>
              <input
                type="range"
                min={s.min} max={s.max} step={s.step}
                value={local[s.key]}
                onChange={e => handleSlider(s.key, e.target.value)}
              />
              <span className="slider-display">
                {Number(local[s.key]).toFixed(s.step < 0.1 ? 2 : s.step === 1 ? 0 : 2)}
                {s.unit && <span style={{ fontSize: 10, opacity: 0.6, marginLeft: 2 }}>{s.unit}</span>}
              </span>
            </div>
          ))}

          {/* Current gains summary */}
          <div style={{
            marginTop: 12, padding: 10, background: '#09101a',
            borderRadius: 4, border: '1px solid #1e2535',
            fontFamily: 'Share Tech Mono', fontSize: 12, color: '#475569',
            lineHeight: 1.8
          }}>
            <div>Kp = <span style={{ color: '#f59e0b' }}>{local.Kp.toFixed(3)}</span></div>
            <div>Ki = <span style={{ color: '#f59e0b' }}>{local.Ki.toFixed(3)}</span></div>
            <div>Kd = <span style={{ color: '#f59e0b' }}>{local.Kd.toFixed(3)}</span></div>
          </div>
        </div>
      </div>

      {/* ── Right: Recipe Manager ─────────── */}
      <div className="panel">
        <div className="panel-header">
          <span className="panel-title"><span className="dot" />RECIPE STORE</span>
          <span style={{ fontSize: 11, color: '#475569', fontFamily: 'Share Tech Mono' }}>
            {recipes.length} saved
          </span>
        </div>
        <div className="panel-body">
          {/* Save current as recipe */}
          <div className="flex gap-8 mb-12">
            <input
              type="text"
              placeholder="Recipe name…"
              value={recipeName}
              onChange={e => setRecipeName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && saveRecipe()}
              style={{ flex: 1 }}
            />
            <button
              className="btn btn-amber btn-sm"
              onClick={saveRecipe}
              disabled={saving || !recipeName.trim()}
            >
              SAVE
            </button>
          </div>

          <div className="section-sep" />

          {/* Recipe list */}
          <div className="recipe-list">
            {recipes.length === 0 && (
              <div style={{ color: '#334155', fontFamily: 'Share Tech Mono', fontSize: 12, textAlign: 'center', padding: 16 }}>
                No recipes saved yet.
              </div>
            )}
            {recipes.map(r => (
              <div key={r.id} className="recipe-item">
                <div>
                  <div className="recipe-name">{r.name}</div>
                  <div className="recipe-vals">
                    Kp={r.kp.toFixed(3)} Ki={r.ki.toFixed(3)} Kd={r.kd.toFixed(3)}
                  </div>
                </div>
                <div className="flex gap-8">
                  <button className="btn btn-primary btn-sm" onClick={() => loadRecipe(r)}>LOAD</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => deleteRecipe(r.id)}>DEL</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
