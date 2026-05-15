import { useState, useEffect } from 'react'
import { useMotorSocket } from './hooks/useMotorSocket'
import Header from './components/layout/Header'
import NavTabs from './components/layout/NavTabs'
import LiveDashboard from './components/scada/LiveDashboard'
import AutoTuneWizard from './components/autotune/AutoTuneWizard'
import History from './components/RunHistory'
import Settings from './components/Settings'
import AlarmLog from './components/scada/AlarmLog'

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  
  // Initialize WebSocket connection
  useMotorSocket()

  return (
    <div className="scada-root">
      <Header />
      <NavTabs activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="main-content">
        {activeTab === 'dashboard' && <LiveDashboard />}
        {activeTab === 'autotune' && <AutoTuneWizard />}
        {activeTab === 'history' && <History />}
        {activeTab === 'settings' && <Settings />}
        {activeTab === 'alarms' && (
          <div style={{ maxWidth: 800, margin: '0 auto', height: 'calc(100vh - 150px)' }}>
            <AlarmLog />
          </div>
        )}
      </main>
      
      <footer style={{
        padding: '8px 20px',
        background: 'var(--bg-panel)',
        borderTop: '1px solid var(--border)',
        display: 'flex', justifyContent: 'space-between',
        fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)'
      }}>
        <span>PID-SCADA v3.0 &middot; Electric Cyan</span>
        <span>PORTFOLIO BUILD</span>
      </footer>
    </div>
  )
}
