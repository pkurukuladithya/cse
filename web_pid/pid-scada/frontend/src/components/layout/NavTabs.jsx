import { Activity, Settings, Zap, History, Bell } from 'lucide-react'
import { useScadaStore } from '../../store/useScadaStore'

const TABS = [
  { id: 'dashboard', label: 'Live SCADA', icon: Activity },
  { id: 'autotune', label: 'Auto-Tune', icon: Zap },
  { id: 'history', label: 'Run History', icon: History },
  { id: 'settings', label: 'Settings', icon: Settings },
]

export default function NavTabs({ activeTab, onTabChange }) {
  const unackedCount = useScadaStore(s => s.unackedCount)

  return (
    <nav className="nav-tabs">
      {TABS.map(tab => {
        const Icon = tab.icon
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            className={`nav-tab ${isActive ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <Icon size={16} />
            {tab.label}
          </button>
        )
      })}
      
      {/* Alarms Tab is special (shows count on the right) */}
      <div style={{ flex: 1 }} />
      <button
        className={`nav-tab ${activeTab === 'alarms' ? 'active' : ''}`}
        onClick={() => onTabChange('alarms')}
        style={{ color: unackedCount > 0 ? 'var(--red)' : '' }}
      >
        <Bell size={16} />
        ALARM LOG
        {unackedCount > 0 && <span className="tab-badge">{unackedCount}</span>}
      </button>
    </nav>
  )
}
