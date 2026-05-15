import { create } from 'zustand'

export const useScadaStore = create((set, get) => ({
  // Connection
  wsStatus: 'disconnected', // 'connecting' | 'connected' | 'disconnected'
  setWsStatus: (s) => set({ wsStatus: s }),

  // Live telemetry (updated 20Hz)
  telemetry: {
    rpm: 0,
    pwm: 0,
    error: 0,
    setpoint: 60,
    phase: 'idle',
    running: false,
    ts: 0,
    kp: 0, ki: 0, kd: 0,
    rise_time: null,
    overshoot: 0,
    settle_time: null,
    itae: 0,
    pwm_mean: 0
  },
  updateTelemetry: (data) => set({ telemetry: data }),

  // Trend Chart Buffer
  trendBuffer: [],
  pushTrendData: (point) => set(state => {
    const next = [...state.trendBuffer, point]
    if (next.length > 600) next.shift() // Keep last 600 points (30s at 20Hz)
    return { trendBuffer: next }
  }),
  clearTrendBuffer: () => set({ trendBuffer: [] }),

  // Alarms
  alarms: [],
  unackedCount: 0,
  addAlarm: (alarm) => set(state => {
    const nextAlarms = [alarm, ...state.alarms].slice(0, 50)
    return {
      alarms: nextAlarms,
      unackedCount: state.unackedCount + 1
    }
  }),
  ackAlarms: () => set({ unackedCount: 0 }),

  // Auto-Tune State
  tuneState: 'idle', // 'idle' | 'running' | 'complete' | 'error'
  tuneProgress: { elapsed: 0, total: 60, peaks_found: 0, progress: 0 },
  tuneResult: null,
  updateTuneProgress: (data) => set({
    tuneState: data.status,
    tuneProgress: {
      elapsed: data.elapsed,
      total: data.total,
      peaks_found: data.peaks_found,
      progress: data.progress
    }
  }),
  setTuneResult: (result) => set({ tuneResult: result, tuneState: 'complete' }),
  resetTuneState: () => set({
    tuneState: 'idle',
    tuneResult: null,
    tuneProgress: { elapsed: 0, total: 60, peaks_found: 0, progress: 0 }
  }),

  // Action Publisher (set by useMotorSocket)
  sendCommand: () => console.warn('sendCommand not initialized yet'),
  setSendCommand: (fn) => set({ sendCommand: fn })
}))
