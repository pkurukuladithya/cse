export function computeRiseTime(data, setpoint) {
  const start = data.find((point) => point.rpm >= setpoint * 0.1);
  const end = data.find((point) => point.rpm >= setpoint * 0.9);
  if (!start || !end) {
    return null;
  }
  return Math.max(0, end.ts - start.ts);
}

export function computeOvershoot(data, setpoint) {
  const peak = Math.max(...data.map((point) => point.rpm));
  if (setpoint <= 0) return null;
  return Math.max(0, ((peak - setpoint) / setpoint) * 100);
}

export function computeSettleTime(data, setpoint) {
  const within = data.filter((point) => Math.abs(point.rpm - setpoint) <= setpoint * 0.02);
  if (!within.length) return null;
  return Math.max(0, within[within.length - 1].ts - within[0].ts);
}
