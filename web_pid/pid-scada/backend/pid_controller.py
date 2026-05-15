"""
pid_controller.py
Full industrial PID controller with:
  - Anti-windup (integral clamping when output saturated)
  - Derivative on measurement (avoids derivative kick on setpoint steps)
  - Bumpless parameter transfer (recalculate integral on gain change)
  - Phase tracking: idle → ramp → stable
  - ITAE accumulator for KPI reporting
Runs in a background daemon thread at SAMPLE_TIME intervals.
"""
import threading
import time
from collections import deque

import logger
from config import (
    SAMPLE_TIME, MAX_PWM, MIN_PWM, MAX_INTEGRAL,
    SETTLING_BAND, SETTLE_CONFIRM, MAX_SAFE_RPM,
    DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_SP,
)

MOVING_AVG_N = 7      # Moving average filter window
DB_LOG_EVERY = 5      # Log to SQLite every N ticks (250ms)


class PIDController:
    def __init__(self, motor, shared_state: dict):
        self.motor = motor
        self.state = shared_state
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # ─────────────────────────────────────────────
    # PID Background Loop
    # ─────────────────────────────────────────────
    def _loop(self):
        integral     = 0.0
        last_pv      = 0.0     # previous process variable (for D-on-measurement)
        last_output  = 0.0     # for bumpless transfer
        rpm_history  = deque(maxlen=MOVING_AVG_N)

        # Performance tracking
        max_rpm      = 0.0
        itae_acc     = 0.0
        pwm_acc      = 0.0
        pwm_samples  = 0
        last_target  = -1.0
        target_start = 0.0
        time_in_band = None
        is_settled   = False
        tick_count   = 0

        # Last known gains (for bumpless transfer detection)
        last_kp, last_ki, last_kd = None, None, None

        while True:
            # ── IDLE ─────────────────────────────────
            if not self.state.get("running", False):
                self.motor.stop()
                time.sleep(0.1)
                rpm_history.clear()
                integral    = 0.0
                last_pv     = 0.0
                last_output = 0.0
                max_rpm     = 0.0
                itae_acc    = 0.0
                pwm_acc     = 0.0
                pwm_samples = 0
                last_target = -1.0
                is_settled  = False
                time_in_band = None
                self.state["phase"] = "idle"
                continue

            loop_start = time.time()
            tick_count += 1

            # ── 1. Read encoder → RPM ─────────────────
            count   = self.motor.read_and_reset_count()
            raw_rpm = self.motor.count_to_rpm(count, SAMPLE_TIME)
            self.state["actual_rpm"] = raw_rpm

            # ── 2. Moving-average smoothing ───────────
            rpm_history.append(raw_rpm)
            smoothed = sum(rpm_history) / len(rpm_history)
            self.state["smoothed_rpm"] = smoothed

            # ── 3. Safety cutoff ──────────────────────
            if raw_rpm > MAX_SAFE_RPM:
                self.state["running"] = False
                msg = f"SAFETY CUTOFF: {raw_rpm:.1f} RPM > {MAX_SAFE_RPM} RPM"
                self.state["alarm"] = {"level": "critical", "message": msg}
                logger.log_alarm("critical", msg)
                self.motor.stop()
                continue

            # ── 4. Setpoint & Phase ───────────────────
            target = float(self.state.get("setpoint", DEFAULT_SP))

            if target != last_target:
                # Setpoint changed — reset tracking
                max_rpm      = smoothed
                last_target  = target
                target_start = time.time()
                time_in_band = None
                is_settled   = False
                itae_acc     = 0.0
                pwm_acc      = 0.0
                pwm_samples  = 0
                self.state["rise_time"]   = None
                self.state["settle_time"] = None
                self.state["overshoot"]   = 0.0
                self.state["itae"]        = 0.0
                self.state["phase"]       = "ramp"
                # Bumpless: keep integral consistent
                # (integral will be recalculated below if gains also changed)

            # Phase assignment
            if target > 0:
                elapsed = time.time() - target_start
                if is_settled:
                    self.state["phase"] = "stable"
                elif elapsed < 0.5:
                    self.state["phase"] = "ramp"
                else:
                    self.state["phase"] = "tuning"
            else:
                self.state["phase"] = "idle"

            # ── 5. Gain bumpless transfer ─────────────
            Kp = float(self.state.get("kp", DEFAULT_KP))
            Ki = float(self.state.get("ki", DEFAULT_KI))
            Kd = float(self.state.get("kd", DEFAULT_KD))

            if last_kp is not None and (Kp != last_kp or Ki != last_ki or Kd != last_kd):
                # Bumpless: recalculate integral so output doesn't jump
                # integral_new = (last_output - Kp*error) / Ki  (if Ki>0)
                error_now = target - smoothed
                if Ki > 0:
                    integral = (last_output - Kp * error_now) / Ki
                    integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral))

            last_kp, last_ki, last_kd = Kp, Ki, Kd

            # ── 6. PID computation ────────────────────
            error = target - smoothed

            P_out = Kp * error

            # Derivative on measurement (not error) → no kick on SP step
            d_pv   = smoothed - last_pv
            D_out  = -Kd * (d_pv / SAMPLE_TIME)

            # Integral with anti-windup
            raw_output = P_out + Ki * integral + D_out
            if raw_output >= MAX_PWM or raw_output <= MIN_PWM:
                # Output is saturated — freeze integral (clamping anti-windup)
                pass
            else:
                integral += error * SAMPLE_TIME
                integral  = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral))

            I_out  = Ki * integral
            output = max(MIN_PWM, min(MAX_PWM, P_out + I_out + D_out))

            self.motor.set_pwm(output)
            last_pv     = smoothed
            last_output = output
            self.state["pwm"]   = round(output, 2)
            self.state["error"] = round(error,  2)

            # ── 7. Performance metrics ────────────────
            if target > 0:
                # Overshoot
                if smoothed > max_rpm:
                    max_rpm = smoothed
                overshoot = max(0.0, (max_rpm - target) / target * 100.0)
                self.state["overshoot"] = round(overshoot, 2)

                # ITAE — Integral of Time × Absolute Error
                t_elapsed = time.time() - target_start
                itae_acc += t_elapsed * abs(error) * SAMPLE_TIME
                self.state["itae"] = round(itae_acc, 4)

                # Rise time: first time smoothed crosses 90% of setpoint
                if self.state.get("rise_time") is None and smoothed >= 0.9 * target:
                    self.state["rise_time"] = round(t_elapsed, 3)

                # Settling time: 2% band + must hold for 0.5s
                lo = target * (1 - SETTLING_BAND)
                hi = target * (1 + SETTLING_BAND)
                if not is_settled:
                    if lo <= smoothed <= hi:
                        if time_in_band is None:
                            time_in_band = time.time()
                        elif (time.time() - time_in_band) >= SETTLE_CONFIRM:
                            is_settled = True
                            self.state["settle_time"] = round(time_in_band - target_start, 3)
                    else:
                        time_in_band = None
                        self.state["settle_time"] = round(t_elapsed, 3)

                # Mean PWM tracking
                pwm_acc     += output
                pwm_samples += 1
                self.state["pwm_mean"] = round(pwm_acc / pwm_samples, 2)

            # ── 8. SQLite log every 250ms ─────────────
            if tick_count % DB_LOG_EVERY == 0:
                logger.log_run(
                    setpoint    = target,
                    kp=Kp, ki=Ki, kd=Kd,
                    rise_time   = self.state.get("rise_time"),
                    overshoot   = self.state.get("overshoot"),
                    itae        = self.state.get("itae"),
                    settle_time = self.state.get("settle_time"),
                    pwm_mean    = self.state.get("pwm_mean"),
                    source      = self.state.get("run_source", "manual"),
                )

            # ── 9. Strict 50ms timing ─────────────────
            elapsed = time.time() - loop_start
            sleep_t = SAMPLE_TIME - elapsed
            if sleep_t > 0:
                time.sleep(sleep_t)
