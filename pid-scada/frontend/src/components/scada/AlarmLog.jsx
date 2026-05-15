import { AnimatePresence, motion } from 'framer-motion';
import { Bell, CheckCircle2 } from 'lucide-react';
import { useScadaStore } from '../../store/useScadaStore.js';

function AlarmLog() {
  const alarms = useScadaStore((state) => state.alarms);
  const ackAlarm = useScadaStore((state) => state.ackAlarm);

  return (
    <div className="panel p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="card-label">Alarm log</div>
        <Bell className="text-accent" />
      </div>
      <div className="space-y-3 overflow-y-auto max-h-72">
        <AnimatePresence initial={false}>
          {alarms.map((alarm) => (
            <motion.div
              key={alarm.id}
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className={`rounded-2xl border-l-4 p-4 ${alarm.level === 'critical' ? 'border-red' : alarm.level === 'warn' ? 'border-amber' : 'border-green'} bg-bg-surface`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm text-white">{alarm.message}</p>
                  <p className="mt-1 text-xs text-text-secondary text-mono">{new Date(alarm.ts * 1000).toLocaleTimeString()}</p>
                </div>
                <button className="btn-outline text-text-secondary" onClick={() => ackAlarm(alarm.id)}>
                  <CheckCircle2 size={16} />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default AlarmLog;
