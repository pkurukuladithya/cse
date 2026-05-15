import { useEffect } from 'react';
import { useScadaStore } from '../store/useScadaStore.js';

export default function useTrendBuffer() {
  const trendBuffer = useScadaStore((state) => state.trendBuffer);

  useEffect(() => {
    if (trendBuffer.length > 600) {
      useScadaStore.setState({ trendBuffer: trendBuffer.slice(-600) });
    }
  }, [trendBuffer]);

  return trendBuffer;
}
