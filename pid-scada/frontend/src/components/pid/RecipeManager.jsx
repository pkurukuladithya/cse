import { useState } from 'react';
import { useScadaStore } from '../../store/useScadaStore.js';

function RecipeManager({ currentParams }) {
  const recipes = useScadaStore((state) => state.recipes);
  const setRecipes = useScadaStore((state) => state.setRecipes);
  const [name, setName] = useState('New recipe');
  const sendCommand = useScadaStore((state) => state.sendCommand) || (() => {});

  const saveCurrent = async () => {
    const payload = { name, kp: currentParams.kp, ki: currentParams.ki, kd: currentParams.kd, notes: 'Saved from live dashboard' };
    await fetch('/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const response = await fetch('/api/recipes');
    setRecipes(await response.json());
  };

  const loadRecipe = (recipe) => {
    sendCommand('load_recipe', { id: recipe.id });
  };

  return (
    <div className="rounded-3xl border border-[rgba(255,255,255,0.08)] bg-bg-surface p-4">
      <div className="card-label mb-4">Recipe manager</div>
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="rounded-xl border border-[rgba(255,255,255,0.08)] bg-bg-panel px-3 py-2 text-sm text-white"
          />
          <button onClick={saveCurrent} className="btn-outline btn-green w-full">
            Save current
          </button>
        </div>
        <div className="space-y-2">
          {recipes.slice(0, 5).map((recipe) => (
            <button key={recipe.id} onClick={() => loadRecipe(recipe)} className="w-full rounded-2xl border border-[rgba(255,255,255,0.08)] px-4 py-3 text-left text-sm text-white">
              <div className="flex items-center justify-between">
                <span>{recipe.name}</span>
                <span className="text-text-secondary text-mono">{recipe.kp}/{recipe.ki}/{recipe.kd}</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default RecipeManager;
