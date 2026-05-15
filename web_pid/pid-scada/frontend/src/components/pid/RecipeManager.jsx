import { useState, useEffect } from 'react'
import { Save, Trash2, Download } from 'lucide-react'
import { useScadaStore } from '../../store/useScadaStore'

export default function RecipeManager({ currentParams }) {
  const [recipes, setRecipes] = useState([])
  const [newRecipeName, setNewRecipeName] = useState('')
  const sendCommand = useScadaStore(s => s.sendCommand)

  const fetchRecipes = () => {
    fetch('/api/recipes')
      .then(res => res.json())
      .then(setRecipes)
      .catch(console.error)
  }

  useEffect(() => {
    fetchRecipes()
  }, [])

  const handleSave = async () => {
    if (!newRecipeName) return
    try {
      await fetch('/api/recipes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newRecipeName,
          kp: currentParams.kp,
          ki: currentParams.ki,
          kd: currentParams.kd
        })
      })
      setNewRecipeName('')
      fetchRecipes()
    } catch (e) {
      console.error(e)
    }
  }

  const handleDelete = async (id) => {
    try {
      await fetch(`/api/recipes/${id}`, { method: 'DELETE' })
      fetchRecipes()
    } catch (e) {
      console.error(e)
    }
  }

  const handleLoad = (id) => {
    sendCommand('load_recipe', { id })
  }

  return (
    <div className="mt-10" style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
      <div className="text-muted" style={{ fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
        Recipe Management
      </div>
      
      <div className="flex gap-8 mb-8">
        <input 
          type="text" 
          placeholder="New recipe name..." 
          value={newRecipeName}
          onChange={e => setNewRecipeName(e.target.value)}
        />
        <button className="btn-ghost btn-sm flex align-center gap-8" onClick={handleSave}>
          <Save size={14} /> SAVE
        </button>
      </div>

      <div className="recipe-list">
        {recipes.map(r => (
          <div key={r.id} className="recipe-item">
            <div>
              <div className="recipe-name">{r.name}</div>
              <div className="recipe-vals">Kp:{r.kp.toFixed(2)} Ki:{r.ki.toFixed(2)} Kd:{r.kd.toFixed(2)}</div>
            </div>
            <div className="flex gap-8">
              <button className="btn-ghost btn-sm" onClick={() => handleLoad(r.id)} title="Load">
                <Download size={14} />
              </button>
              <button className="btn-ghost btn-sm" onClick={() => handleDelete(r.id)} style={{ color: 'var(--red)' }} title="Delete">
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
