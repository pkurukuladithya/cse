import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/layout/Header.jsx';
import NavTabs from './components/layout/NavTabs.jsx';
import LiveDashboard from './components/scada/LiveDashboard.jsx';
import AutoTuneWizard from './components/autotune/AutoTuneWizard.jsx';
import { useScadaStore } from './store/useScadaStore.js';
import useMotorSocket from './hooks/useMotorSocket.js';

const tabs = ['Live', 'Auto-Tune', 'History', 'Settings'];

function App() {
  const [activeTab, setActiveTab] = useState('Live');
  const ws = useMotorSocket();
  const recipes = useScadaStore((state) => state.recipes);
  const alarms = useScadaStore((state) => state.alarms);

  useEffect(() => {
    document.title = 'PID SCADA';
  }, []);

  const tabBody = useMemo(() => {
    switch (activeTab) {
      case 'Auto-Tune':
        return <AutoTuneWizard />;
      case 'History':
        return <div className="panel">History tab is coming soon.</div>;
      case 'Settings':
        return <div className="panel">Settings panel placeholder.</div>;
      default:
        return <LiveDashboard />;
    }
  }, [activeTab]);

  return (
    <div className="app-shell">
      <Header />
      <NavTabs tabs={tabs} active={activeTab} onChange={setActiveTab} />
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.25 }}
          className="tab-content"
        >
          {tabBody}
        </motion.div>
      </AnimatePresence>
      <footer className="app-footer">
        PID-SCADA · React + FastAPI · Raspberry Pi 4 · TB6612FNG
      </footer>
    </div>
  );
}

export default App;
