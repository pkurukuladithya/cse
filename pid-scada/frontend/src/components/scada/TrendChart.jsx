import { ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts';

function tooltipFormatter(value) {
  return [`${value.toFixed(1)}`, 'RPM'];
}

function TrendChart({ data, setpoint }) {
  return (
    <div className="panel p-4" style={{ height: '360px' }}>
      <div className="card-label mb-3">Process variable · real-time trend</div>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid stroke="rgba(0,200,232,0.06)" vertical={false} />
          <XAxis dataKey="ts" tick={{ fill: '#607a90', fontFamily: 'Share Tech Mono', fontSize: 11 }} tickFormatter={(time) => new Date(time).toLocaleTimeString()} axisLine={false} tickLine={false} />
          <YAxis domain={[0, 130]} ticks={[20, 40, 60, 80, 100, 120]} tick={{ fill: '#607a90', fontFamily: 'Share Tech Mono', fontSize: 11 }} axisLine={false} tickLine={false} />
          <ReferenceLine y={setpoint} stroke="#f5a623" strokeDasharray="8 4" strokeWidth={1.5} />
          <Line dataKey="rpm" stroke="#00c8e8" strokeWidth={2} dot={false} activeDot={false} fill="#00c8e8" fillOpacity={0.06} />
          <Tooltip wrapperStyle={{ borderRadius: 16, backgroundColor: '#0b1723', borderColor: '#0a1220' }} labelFormatter={(time) => new Date(time).toLocaleTimeString()} formatter={tooltipFormatter} contentStyle={{ background: '#0b1723', border: '1px solid rgba(0,200,232,0.12)', color: '#d4e8f0', fontFamily: 'Share Tech Mono' }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrendChart;
