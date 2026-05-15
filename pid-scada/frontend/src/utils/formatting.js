export const formatRpm = (value) => `${value.toFixed(1)} rpm`;
export const formatPct = (value) => `${value.toFixed(1)} %`;
export const formatTime = (seconds) => (seconds == null ? '—' : `${seconds.toFixed(1)}s`);
export const formatNumber = (value, digits = 1) => (value == null ? '—' : value.toFixed(digits));
