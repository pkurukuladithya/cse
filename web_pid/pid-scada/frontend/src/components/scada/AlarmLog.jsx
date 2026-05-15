import { motion, AnimatePresence } from 'framer-motion'
import { useScadaStore } from '../../store/useScadaStore'

export default function AlarmLog() {
  const alarms = useScadaStore(s => s.alarms)
  const ackAlarms = useScadaStore(s => s.ackAlarms)

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="panel-header">
        <div className="panel-title">ALARM LOG</div>
        <button className="btn-ghost btn-sm" onClick={ackAlarms}>ACK ALL</button>
      </div>
      
      <div className="panel-body" style={{ flex: 1, padding: 0, overflowY: 'auto', maxHeight: 200 }}>
        {alarms.length === 0 ? (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 11, fontStyle: 'italic' }}>
            No recent alarms.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <AnimatePresence>
              {alarms.map((alarm, idx) => (
                <motion.div
                  key={`${alarm.ts}-${idx}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={`alarm-item ${alarm.level}`}
                >
                  <div className={`alarm-level ${alarm.level}`}>
                    {alarm.level.toUpperCase()}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div className="text-secondary" style={{ fontSize: 12 }}>{alarm.message}</div>
                    <div className="text-muted text-mono" style={{ fontSize: 10, marginTop: 4 }}>
                      {new Date(alarm.ts * 1000).toLocaleString('en-GB')}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  )
}
