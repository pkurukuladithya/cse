import { useEffect, useRef } from 'react';
import { useScadaStore } from '../store/useScadaStore.js';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:5000/ws';

function useMotorSocket() {
  const retryRef = useRef(0);
  const wsRef = useRef(null);
  const setWsStatus = useScadaStore((state) => state.setWsStatus);
  const updateTelemetry = useScadaStore((state) => state.updateTelemetry);
  const addAlarm = useScadaStore((state) => state.addAlarm);
  const setTuneState = useScadaStore((state) => state.setTuneState);
  const setTuneProgress = useScadaStore((state) => state.setTuneProgress);
  const setTuneResult = useScadaStore((state) => state.setTuneResult);

  useEffect(() => {
    let mounted = true;
    let reconnectTimer = null;

    const connect = () => {
      if (!mounted) return;
      setWsStatus('connecting');
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.addEventListener('open', () => {
        retryRef.current = 0;
        setWsStatus('connected');
      });

      ws.addEventListener('message', (event) => {
        try {
          const payload = JSON.parse(event.data);
          switch (payload.type) {
            case 'telemetry':
              updateTelemetry(payload.data);
              break;
            case 'alarm':
              addAlarm(payload.data);
              break;
            case 'autotune_progress':
              setTuneState('running');
              setTuneProgress(payload.data);
              break;
            case 'autotune_result':
              setTuneState('complete');
              setTuneResult(payload.data);
              break;
            default:
              break;
          }
        } catch (error) {
          console.warn('Invalid WS payload', error);
        }
      });

      ws.addEventListener('close', () => {
        if (!mounted) return;
        setWsStatus('disconnected');
        const delay = Math.min(30000, 1000 * 2 ** retryRef.current);
        retryRef.current += 1;
        reconnectTimer = window.setTimeout(connect, delay);
      });

      ws.addEventListener('error', () => {
        setWsStatus('error');
        ws.close();
      });
    };

    connect();

    return () => {
      mounted = false;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, [setWsStatus, updateTelemetry, addAlarm, setTuneState, setTuneProgress, setTuneResult]);

  const sendCommand = (action, params = {}) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return;
    }
    ws.send(JSON.stringify({ action, params }));
  };

  return {
    sendCommand,
    connectionState: useScadaStore((state) => state.wsStatus),
  };
}

export default useMotorSocket;
