import math
import threading
import time
from typing import Callable, Dict, List, Optional

from config import AUTOTUNE_DURATION, AUTOTUNE_PROGRESS_INTERVAL, MAX_PWM, MIN_PWM


class AutoTuner:
    def __init__(self, read_pv: Callable[[], float], set_output: Callable[[float], None]):
        self.read_pv = read_pv
        self.set_output = set_output
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self, setpoint: float, relay_amp: float, progress_callback: Optional[Callable[[Dict], None]] = None) -> Dict:
        start_time = time.time()
        self._stop_event.clear()

        samples: List[Dict] = []
        peaks: List[Dict] = []
        last_derivative = 0.0
        last_pv = self.read_pv()
        last_toggle = start_time
        period_times: List[float] = []
        high_output = min(MAX_PWM, max(MIN_PWM, 50.0 + relay_amp))
        low_output = min(MAX_PWM, max(MIN_PWM, 50.0 - relay_amp))
        current_output = high_output
        self.set_output(current_output)

        while time.time() - start_time < AUTOTUNE_DURATION and not self._stop_event.is_set():
            now = time.time()
            pv = self.read_pv()
            dt = now - last_toggle
            derivative = (pv - last_pv) / max(1e-4, now - start_time)
            samples.append({"time": now, "pv": pv, "output": current_output})

            if len(samples) > 2:
                previous = samples[-2]
                prev_deriv = (previous["pv"] - samples[-3]["pv"]) / max(1e-4, previous["time"] - samples[-3]["time"])
                if prev_deriv > 0 and derivative <= 0:
                    peaks.append({"time": now, "pv": pv, "type": "peak"})
                elif prev_deriv < 0 and derivative >= 0:
                    peaks.append({"time": now, "pv": pv, "type": "valley"})

            if pv >= setpoint + relay_amp * 0.25 and current_output != low_output:
                current_output = low_output
                self.set_output(current_output)
                period_times.append(now)
            elif pv <= setpoint - relay_amp * 0.25 and current_output != high_output:
                current_output = high_output
                self.set_output(current_output)
                period_times.append(now)

            if progress_callback and now - start_time >= len(period_times) * AUTOTUNE_PROGRESS_INTERVAL:
                progress_callback({
                    "elapsed": round(now - start_time, 1),
                    "total": AUTOTUNE_DURATION,
                    "peaks_found": len(peaks),
                    "status": "oscillating" if len(peaks) >= 2 else "warming up"
                })
            last_pv = pv
            time.sleep(0.05)

        self.set_output(0.0)

        amplitude = self._estimate_amplitude(peaks)
        tu = self._estimate_period(period_times)
        ku = 0.0
        if amplitude > 0 and tu > 0:
            ku = (4.0 * relay_amp) / (math.pi * amplitude)

        kp = round(0.60 * ku, 4)
        ki = round(1.20 * ku / tu if tu > 0 else 0.0, 4)
        kd = round(0.075 * ku * tu if tu > 0 else 0.0, 4)

        confidence = self._confidence_score(period_times)
        result = {
            "kp": kp,
            "ki": ki,
            "kd": kd,
            "ku": round(ku, 4),
            "tu": round(tu, 4),
            "oscillation_amplitude": round(amplitude, 4),
            "confidence_score": round(confidence, 3),
        }
        return result

    def _estimate_amplitude(self, peaks: List[Dict]) -> float:
        values = [p["pv"] for p in peaks if p["type"] in {"peak", "valley"}]
        if len(values) < 2:
            return 0.0
        paired = []
        for i in range(1, len(values)):
            paired.append(abs(values[i] - values[i - 1]))
        return sum(paired) / len(paired) if paired else 0.0

    def _estimate_period(self, periods: List[float]) -> float:
        if len(periods) < 2:
            return 0.0
        intervals = [periods[i] - periods[i - 1] for i in range(1, len(periods))]
        return sum(intervals) / len(intervals) if intervals else 0.0

    def _confidence_score(self, periods: List[float]) -> float:
        if len(periods) < 3:
            return 0.5
        intervals = [periods[i] - periods[i - 1] for i in range(1, len(periods))]
        mean = sum(intervals) / len(intervals)
        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        score = max(0.0, 1.0 - min(1.0, variance / (mean + 1e-4)))
        return score
