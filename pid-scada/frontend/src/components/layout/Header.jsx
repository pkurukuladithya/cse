import { useEffect, useState } from 'react';
import { Cpu, Clock3, Wifi } from 'lucide-react';

function Header() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const id = window.setInterval(() => setTime(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div className="panel flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p className="text-[0.72rem] uppercase tracking-[0.3em] text-text-secondary mb-2">Industrial SCADA · PID Control System</p>
        <h1 className="text-3xl font-semibold text-white">Motor Control Dashboard</h1>
        <p className="mt-2 text-sm text-text-secondary">RPi 4 · TB6612FNG · N20 encoder motor · 5.28V supply</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
        <div className="panel bg-bg-surface p-4">
          <div className="flex items-center gap-2 text-accent text-sm uppercase tracking-[0.22em]">Status</div>
          <div className="mt-3 text-2xl font-semibold text-green">Connected</div>
        </div>
        <div className="panel bg-bg-surface p-4">
          <div className="flex items-center gap-2 text-accent text-sm uppercase tracking-[0.22em]">Node</div>
          <div className="mt-3 text-xl font-semibold">RPi4-B01</div>
        </div>
        <div className="panel bg-bg-surface p-4 flex items-center gap-3">
          <Clock3 className="text-accent" />
          <span className="text-xl font-semibold text-white">{time.toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
}

export default Header;
