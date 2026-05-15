/**
 * PIDPanel.jsx - FIXED
 * Key fix: sliders use LOCAL state only. WebSocket state does NOT overwrite
 * slider values while the user is interacting. Syncs only on first load
 * and when auto-tuner applies new values (detected by a version counter).
 */
import { useState, useEffect, useRef } from 'react'

export default function PIDPanel({ motorState, sendUpdate }) {
  const [kp, setKp] = useState(motorState.Kp)
  const [ki, setKi] = useState(motorState.Ki)
  const [kd, setKd] = useState(motorState.Kd)
  const [recipes, setRecipes]       = useState([])
  const [recipeName, setRecipeName] = useState('')
  const [saving, setSaving]         = useState(false)

  // Track last auto-tune result version so we only sync when AT applies new values
  const lastAtResult = useRef(null)

  useEffect(() => {
    const result = motorState.autotune?.result
    if (result && result !== lastAtResult.current) {
      lastAtResult.current = result
      setKp(result.Kp)
      setKi(result.Ki)
      setKd(result.Kd)
    }
  }, [motorState.autotune?.result])

  // Load recipes on mount
  useEffect(() => { fetchRecipes() }, [])

  const fetchRecipes = async () => {
    try {
      const res  = await fetch('/api/recipes')
      const data = await res.json()
      setRecipes(data)
    } catch (_) {}
  }

  // Single handler: update local state + send to backend immediately
  const handleKp = (v) => { setKp(+v); sendUpdate({ Kp: +v }) }
  const handleKi = (v) => { setKi(+v); sendUpdate({ Ki: +v }) }
  const handleKd = (v) => { setKd(+v); sendUpdate({ Kd: +v }) }

  const saveRecipe = async () => {
    if (!recipeName.trim()) return
    setSaving(true)
    await fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: recipeName, kp, ki, kd }),
    })
    setRecipeName('')
    await fetchRecipes()
    setSaving(false)
  }

  const loadRecipe = (r) => {
    setKp(r.kp); setKi(r.ki); setKd(r.kd)
    sendUpdate({ Kp: r.kp, Ki: r.ki, Kd: r.kd })
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

          {/* Kp */}
          <div className="slider-row">
            <span className="slider-label">Proportional (Kp)</span>
            <input type="range" min={0} max={10} step={0.05}
              value={kp} onChange={e => handleKp(e.target.value)} />
            <span className="slider-display">{Number(kp).toFixed(2)}</span>
          </div>

          {/* Ki */}
          <div className="slider-row">
            <span className="slider-label">Integral (Ki)</span>
            <input type="range" min={0} max={5} step={0.05}
              value={ki} onChange={e => handleKi(e.target.value)} />
            <span className="slider-display">{Number(ki).toFixed(2)}</span>
          </div>

          {/* Kd */}
          <div className="slider-row">
            <span className="slider-label">Derivative (Kd)</span>
            <input type="range" min={0} max={1} step={0.01}
              value={kd} onChange={e => handleKd(e.target.value)} />
            <span className="slider-display">{Number(kd).toFixed(2)}</span>
          </div>

          {/* Live summary */}
          <div style={{
            marginTop: 14, padding: '12px 14px', background: '#09101a',
            borderRadius: 4, border: '1px solid #1e2535',
            fontFamily: 'Share Tech Mono', fontSize: 13, lineHeight: 2
          }}>
            <div>Kp = <span style={{ color: '#f59e0b' }}>{Number(kp).toFixed(3)}</span></div>
            <div>Ki = <span style={{ color: '#f59e0b' }}>{Number(ki).toFixed(3)}</span></div>
            <div>Kd = <span style={{ color: '#f59e0b' }}>{Number(kd).toFixed(3)}</span></div>
          </div>

          {/* Live actual from backend for comparison */}
          <div style={{
            marginTop: 8, padding: '8px 14px', background: '#09101a',
            borderRadius: 4, border: '1px solid #1e2535',
            fontFamily: 'Share Tech Mono', fontSize: 11, color: '#334155'
          }}>
            Backend active → Kp={motorState.Kp?.toFixed(3)} Ki={motorState.Ki?.toFixed(3)} Kd={motorState.Kd?.toFixed(3)}
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
