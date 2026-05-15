"""
auto_tuner.py
Ziegler-Nichols Relay Feedback auto-tuner.

Method:
  1. Replace PID with an on/off relay around the setpoint.
  2. The motor will oscillate. We measure the period (Pu) and
     the amplitude of oscillation to derive Ku (ultimate gain).
  3. Apply Z-N formulas: Kp=0.6Ku, Ki=1.2Ku/Pu, Kd=0.075*Ku*Pu
"""
import threading
import time
import math
import logger

RELAY_HIGH  = 60.0   # PWM% when error > 0
RELAY_LOW   = 0.0    # PWM% when error < 0
MIN_CYCLES  = 4      # Minimum oscillation cycles to confirm Pu
TIMEOUT_S   = 60.0   # Abort if no stable oscillation in 60s


class AutoTuner:
    def __init__(self, motor, shared_state: dict):
        self.motor  = motor
        self.state  = shared_state
        self._reset()

    def _reset(self):
        self.state["autotune"] = {
            "active":   False,
            "status":   "IDLE",    # IDLE | RUNNING | SUCCESS | FAILED
            "progress": 0,
            "result":   None,       # {"Kp": x, "Ki": y, "Kd": z, "Ku": .., "Pu": ..}
            "log":      []
        }

    def start(self, setpoint_rpm: float):
        if self.state["autotune"]["active"]:
            return {"error": "Auto-tune already running"}
        self._reset()
        self.state["autotune"]["active"] = True
        t = threading.Thread(
            target=self._run,
            args=(setpoint_rpm,),
            daemon=True
        )
        t.start()
        return {"status": "started", "setpoint": setpoint_rpm}

    def _log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.state["autotune"]["log"].append(entry)
        print(f"[AutoTune] {entry}")

    def _run(self, setpoint: float):
        at = self.state["autotune"]
        at["status"] = "RUNNING"
        self._log(f"Starting relay test at setpoint={setpoint:.1f} RPM")

        peaks      = []   # local maxima of RPM
        troughs    = []   # local minima of RPM
        last_relay = None
        start_time = time.time()
        prev_rpm   = 0.0
        direction  = None  # 'up' or 'down'
        rpm_buffer = []

        SAMPLE_DT = 0.05  # 50ms

        while True:
            # ── Timeout guard ───────────────────────
            if time.time() - start_time > TIMEOUT_S:
                at["status"] = "FAILED"
                self._log("FAILED: Timeout — no stable oscillation detected.")
                at["active"] = False
                logger.log_alarm("WARNING", "Auto-tune timed out after 60s.")
                return

            # ── Read current smoothed RPM ────────────
            rpm = self.state.get("smoothed_rpm", 0.0)

            # ── Relay control (hysteresis ±1 RPM) ───
            if rpm < setpoint - 1.0:
                relay = RELAY_HIGH
            elif rpm > setpoint + 1.0:
                relay = RELAY_LOW
            else:
                relay = last_relay if last_relay else RELAY_HIGH

            if relay != last_relay:
                last_relay = relay
                self._log(f"Relay → {relay:.0f}%  RPM={rpm:.1f}")

            self.motor.set_pwm(relay)

            # ── Peak / trough detection ──────────────
            rpm_buffer.append(rpm)
            if len(rpm_buffer) >= 3:
                a, b, c = rpm_buffer[-3], rpm_buffer[-2], rpm_buffer[-1]
                if b > a and b > c:          # local maximum
                    peaks.append((time.time(), b))
                elif b < a and b < c:        # local minimum
                    troughs.append((time.time(), b))

            # ── Progress ─────────────────────────────
            cycles = min(len(peaks), len(troughs))
            at["progress"] = int(min(100, cycles / MIN_CYCLES * 80))

            # ── Check if we have enough cycles ───────
            if len(peaks) >= MIN_CYCLES and len(troughs) >= MIN_CYCLES:
                self._log(f"Collected {len(peaks)} peaks. Calculating Ku, Pu…")
                break

            time.sleep(SAMPLE_DT)

        # ── Calculate Ku and Pu ──────────────────────
        # Pu = average period between successive peaks
        periods = [peaks[i+1][0] - peaks[i][0] for i in range(len(peaks)-1)]
        Pu      = sum(periods) / len(periods)

        # Ku from relay method: Ku = (4*d) / (π*a)
        # d = relay amplitude, a = oscillation amplitude (avg peak-trough / 2)
        d = (RELAY_HIGH - RELAY_LOW) / 2.0  # relay amplitude in PWM%
        avg_peak   = sum(p[1] for p in peaks[-MIN_CYCLES:])   / MIN_CYCLES
        avg_trough = sum(t[1] for t in troughs[-MIN_CYCLES:]) / MIN_CYCLES
        a = (avg_peak - avg_trough) / 2.0   # oscillation amplitude in RPM

        if a < 0.5:
            at["status"] = "FAILED"
            self._log("FAILED: Oscillation amplitude too small.")
            at["active"] = False
            return

        Ku = (4 * d) / (math.pi * a)

        # ── Z-N PID formulas ─────────────────────────
        Kp = 0.60 * Ku
        Ki = 1.20 * Ku / Pu
        Kd = 0.075 * Ku * Pu

        result = {
            "Ku": round(Ku, 4),
            "Pu": round(Pu, 4),
            "Kp": round(Kp, 4),
            "Ki": round(Ki, 4),
            "Kd": round(Kd, 4),
        }
        at["result"]   = result
        at["status"]   = "SUCCESS"
        at["progress"] = 100
        at["active"]   = False

        self._log(f"SUCCESS! Ku={Ku:.4f} Pu={Pu:.4f}s → Kp={Kp:.4f} Ki={Ki:.4f} Kd={Kd:.4f}")
        logger.log_alarm("INFO", f"Auto-tune SUCCESS: Kp={Kp:.3f} Ki={Ki:.3f} Kd={Kd:.3f}")

        # Stop relay and hand back to PID
        self.motor.stop()
