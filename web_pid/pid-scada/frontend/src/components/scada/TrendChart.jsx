import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts'
import { useScadaStore } from '../../store/useScadaStore'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#0c1420', border: '1px solid #1e2a3a',
      padding: '8px 12px', fontFamily: 'Share Tech Mono', fontSize: 12,
      boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
    }}>
      <div style={{ color: '#607a90', marginBottom: 4 }}>{payload[0].payload.time}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, marginBottom: 2 }}>
          {p.name}: {Number(p.value).toFixed(1)}
        </div>
      ))}
    </div>
  )
}

export default function TrendChart() {
  const trendData = useScadaStore(s => s.trendBuffer)

  return (
    <div className="panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div className="panel-title"><span className="dot"/>PROCESS VARIABLE &middot; REAL-TIME TREND</div>
        <div className="text-mono" style={{ fontSize: 10, color: 'var(--accent)' }}>
          {trendData.length} PTS
        </div>
      </div>
      <div className="panel-body" style={{ flex: 1, padding: '16px 16px 16px 0', minHeight: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
            <XAxis dataKey="time" hide />
            <YAxis domain={[0, 130]} ticks={[0, 20, 40, 60, 80, 100, 120]} tick={{ fill: '#3a5060', fontSize: 10, fontFamily: 'Share Tech Mono' }} stroke="rgba(255,255,255,0.05)" width={40} />
            <Tooltip content={<CustomTooltip />} isAnimationActive={false} />
            
            {/* Setpoint Line */}
            <Line type="stepAfter" dataKey="setpoint" name="SP" stroke="rgba(155,109,255,0.5)" strokeWidth={1} strokeDasharray="4 4" dot={false} isAnimationActive={false} />
            
            {/* Actual RPM Line */}
            <Line type="monotone" dataKey="rpm" name="PV" stroke="var(--accent)" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
