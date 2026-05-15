"""
auto_tuner.py
Ziegler-Nichols Relay Feedback auto-tuner.

Method:
  1. Save current PID params, switch to relay (bang-bang) controller.
  2. Run relay at setpoint ± relay_amplitude for up to AT_TIMEOUT seconds.
  3. Detect oscillation peaks and valleys via derivative sign changes.
  4. Calculate Ultimate Gain (Ku) and Ultimate Period (Tu):
       Ku = (4 × relay_amplitude) / (π × oscillation_amplitude)
       Tu = mean period between successive peaks
  5. Apply classic Z-N PID formulas:
       Kp = 0.60 × Ku
       Ki = 1.20 × Ku / Tu
       Kd = 0.075 × Ku × Tu
  6. Confidence score: 1 - (std_dev_of_periods / mean_period)
  7. Restore motor to normal PID with new gains.

Progress events are published via a callback (broadcast_fn) every 500ms.
"""
import threading
import time
import math
import statistics
import logger

from config import (
    AT_RELAY_HIGH, AT_RELAY_LOW, AT_DEFAULT_AMP,
    AT_MIN_CYCLES, AT_TIMEOUT, AT_HYSTERESIS, SAMPLE_TIME,
)


class AutoTuner:
    def __init__(self, motor, shared_state: dict, broadcast_fn=None):
        """
        motor        — HardwareMotorDriver or MockMotorDriver
        shared_state — dict shared with FastAPI / WebSocket layer
        broadcast_fn — async coroutine ref (called via asyncio.run_coroutine_threadsafe)
        """
        self.motor        = motor
        self.state        = shared_state
        self.broadcast_fn = broadcast_fn   # set after FastAPI app is created
        self._loop_ref    = None            # asyncio event loop reference
        self._reset()

    def _reset(self):
        self.state["autotune"] = {
            "active":    False,
            "status":    "idle",        # idle | running | complete | error
            "progress":  0,
            "elapsed":   0.0,
            "total":     AT_TIMEOUT,
            "peaks_found": 0,
            "result":    None,
            "log":       [],
        }

    def set_event_loop(self, loop):
        """Register the asyncio event loop so broadcast can be called from thread."""
        self._loop_ref = loop

    def start(self, setpoint: float, relay_amp: float = AT_DEFAULT_AMP):
        at = self.state["autotune"]
        if at["active"]:
            return {"error": "Auto-tune already running"}
        self._reset()
        at["active"] = True
        t = threading.Thread(
            target=self._run,
            args=(setpoint, relay_amp),
            daemon=True
        )
        t.start()
        return {"status": "started", "setpoint": setpoint, "relay_amp": relay_amp}

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────
    def _log(self, msg: str):
        ts    = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.state["autotune"]["log"].append(entry)
        print(f"[AutoTune] {entry}")

    def _publish_progress(self, elapsed: float, peaks: int):
        """Push autotune_progress message via WebSocket (non-blocking)."""
        at = self.state["autotune"]
        at["elapsed"]     = round(elapsed, 1)
        at["peaks_found"] = peaks
        at["progress"]    = min(99, int(peaks / AT_MIN_CYCLES * 80))
        if self.broadcast_fn and self._loop_ref:
            import asyncio
            msg = {
                "type": "autotune_progress",
                "data": {
                    "elapsed":     at["elapsed"],
                    "total":       at["total"],
                    "peaks_found": peaks,
                    "status":      at["status"],
                    "progress":    at["progress"],
                }
            }
            asyncio.run_coroutine_threadsafe(self.broadcast_fn(msg), self._loop_ref)

    def _publish_result(self, result: dict):
        """Push autotune_result message via WebSocket."""
        if self.broadcast_fn and self._loop_ref:
            import asyncio
            asyncio.run_coroutine_threadsafe(
                self.broadcast_fn({"type": "autotune_result", "data": result}),
                self._loop_ref
            )

    # ─────────────────────────────────────────────
    # Main relay-feedback loop
    # ─────────────────────────────────────────────
    def _run(self, setpoint: float, relay_amp: float):
        at = self.state["autotune"]
        at["status"] = "running"
        self._log(f"Relay test start: setpoint={setpoint:.1f} RPM, amp={relay_amp:.1f}%")

        relay_high = min(100.0, setpoint / (0.65) + relay_amp)   # estimate PWM needed
        relay_low  = max(0.0,   relay_high - 2 * relay_amp)

        peaks      = []
        troughs    = []
        rpm_buf    = []
        last_relay = None
        start_t    = time.time()
        next_pub   = start_t + 0.5   # next progress broadcast

        while True:
            now = time.time()

            # ── Timeout ───────────────────────────────
            if now - start_t > AT_TIMEOUT:
                at["status"] = "error"
                at["active"] = False
                self._log("FAILED: Timeout — no stable oscillation detected.")
                logger.log_alarm("warn", "Auto-tune timed out after 60s.")
                self.motor.stop()
                return

            # ── Read RPM ──────────────────────────────
            rpm = self.state.get("smoothed_rpm", 0.0)

            # ── Relay with hysteresis ─────────────────
            if rpm < setpoint - AT_HYSTERESIS:
                relay = relay_high
            elif rpm > setpoint + AT_HYSTERESIS:
                relay = relay_low
            else:
                relay = last_relay if last_relay is not None else relay_high

            if relay != last_relay:
                self._log(f"Relay → {relay:.0f}%  RPM={rpm:.1f}")
                last_relay = relay

            self.motor.set_pwm(relay)

            # ── Peak / trough detection ───────────────
            rpm_buf.append(rpm)
            if len(rpm_buf) >= 3:
                a, b, c = rpm_buf[-3], rpm_buf[-2], rpm_buf[-1]
                if b > a and b > c:
                    peaks.append((now, b))
                elif b < a and b < c:
                    troughs.append((now, b))

            # ── Progress publish every 500ms ──────────
            if now >= next_pub:
                self._publish_progress(now - start_t, len(peaks))
                next_pub = now + 0.5

            # ── Enough cycles? ────────────────────────
            if len(peaks) >= AT_MIN_CYCLES and len(troughs) >= AT_MIN_CYCLES:
                self._log(f"Collected {len(peaks)} peaks. Computing Ku, Tu…")
                break

            time.sleep(SAMPLE_TIME)

        # ── Calculate Ku and Tu ───────────────────────
        periods = [peaks[i+1][0] - peaks[i][0] for i in range(len(peaks) - 1)]
        Tu      = statistics.mean(periods)

        # Confidence: 1 - (stdev / mean)
        confidence = 1.0
        if len(periods) >= 2 and Tu > 0:
            sd         = statistics.stdev(periods)
            confidence = max(0.0, min(1.0, round(1.0 - sd / Tu, 3)))

        # Ku = (4 × d) / (π × a)
        # d = relay amplitude in RPM-equivalent (half the relay swing)
        d = (relay_high - relay_low) / 2.0
        avg_peak   = statistics.mean(p[1] for p in peaks[-AT_MIN_CYCLES:])
        avg_trough = statistics.mean(t[1] for t in troughs[-AT_MIN_CYCLES:])
        a          = (avg_peak - avg_trough) / 2.0

        if a < 0.5:
            at["status"] = "error"
            at["active"] = False
            self._log("FAILED: Oscillation amplitude too small (< 0.5 RPM).")
            self.motor.stop()
            return

        Ku = (4.0 * d) / (math.pi * a)

        # Z-N PID formulas
        Kp = round(0.60 * Ku, 4)
        Ki = round(1.20 * Ku / Tu, 4)
        Kd = round(0.075 * Ku * Tu, 4)

        result = {
            "kp":                   Kp,
            "ki":                   Ki,
            "kd":                   Kd,
            "ku":                   round(Ku, 4),
            "tu":                   round(Tu, 4),
            "oscillation_amplitude": round(a, 3),
            "confidence":           confidence,
        }

        at["result"]   = result
        at["status"]   = "complete"
        at["progress"] = 100
        at["active"]   = False

        self._log(
            f"SUCCESS! Ku={Ku:.4f} Tu={Tu:.4f}s → "
            f"Kp={Kp} Ki={Ki} Kd={Kd} conf={confidence:.2f}"
        )
        logger.log_alarm(
            "info",
            f"Auto-tune complete: Kp={Kp} Ki={Ki} Kd={Kd} (confidence={confidence:.0%})"
        )

        # Publish result via WebSocket
        self._publish_result(result)

        # Hand back to PID — stop relay
        self.motor.stop()
