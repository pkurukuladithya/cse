function NavTabs({ tabs, active, onChange }) {
  return (
    <div className="grid gap-2 sm:grid-cols-4">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={`btn-outline ${active === tab ? 'text-accent border-accent bg-[rgba(0,200,232,0.08)]' : 'text-text-secondary border-[rgba(0,200,232,0.08)]'}`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

export default NavTabs;
