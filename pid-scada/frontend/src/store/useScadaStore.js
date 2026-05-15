import { create } from 'zustand';

export const useScadaStore = create((set) => ({
  wsStatus: 'disconnected',
  telemetry: { rpm: 0, pwm: 0, error: 0, setpoint: 60, phase: 'idle', ts: Date.now() },
  trendBuffer: [],
  pidParams: { kp: 1.0, ki: 1.5, kd: 0.01, setpoint: 60 },
  running: false,
  phase: 'idle',
  tuneState: 'idle',
  tuneProgress: null,
  tuneResult: null,
  alarms: [],
  unackedCount: 0,
  runs: [],
  recipes: [],
  kpis: { riseTime: null, overshoot: null, itae: null, settleTime: null },
  setWsStatus: (status) => set({ wsStatus: status }),
  updateTelemetry: (payload) =>
    set((state) => ({
      telemetry: payload,
      phase: payload.phase,
      running: payload.phase !== 'idle',
      trendBuffer: [...state.trendBuffer.slice(-599), payload],
    })),
  addAlarm: (alarm) =>
    set((state) => ({
      alarms: [alarm, ...state.alarms].slice(0, 50),
      unackedCount: state.unackedCount + (alarm.cleared ? 0 : 1),
    })),
  ackAlarm: (id) =>
    set((state) => ({
      alarms: state.alarms.map((item) => (item.id === id ? { ...item, cleared: 1 } : item)),
      unackedCount: state.alarms.filter((item) => item.id !== id && !item.cleared).length,
    })),
  setPidParams: (params) => set((state) => ({ pidParams: { ...state.pidParams, ...params } })),
  setRecipes: (recipes) => set({ recipes }),
  setRuns: (runs) => set({ runs }),
  setTuneState: (tuneState) => set({ tuneState }),
  setTuneProgress: (tuneProgress) => set({ tuneProgress }),
  setTuneResult: (tuneResult) => set({ tuneResult }),
}));
