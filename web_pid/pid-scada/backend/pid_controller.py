"""
pid_controller.py
PID control loop running in a background threading.Thread at 50ms intervals.
Writes data to SQLite and updates the shared state dict consumed by the WebSocket.
"""
import threading
import time
from collections import deque
import logger

SAMPLE_TIME   = 0.05   # 50ms
MAX_PWM       = 100.0
MAX_INTEGRAL  = 200.0
MOVING_AVG_N  = 7      # 7-point moving average filter
SETTLING_BAND = 0.02   # ±2%
DB_LOG_EVERY  = 5      # log to SQLite every N ticks (every 250ms)


class PIDController:
    def __init__(self, motor, shared_state: dict):
        """
        motor       — HardwareMotorDriver or MockMotorDriver instance
        shared_state — dict shared with FastAPI/WebSocket layer
        """
        self.motor = motor
        self.state = shared_state
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # ─────────────────────────────────────────
    # PID Background Loop
    # ─────────────────────────────────────────
    def _loop(self):
        integral      = 0.0
        prev_error    = 0.0
        rpm_history   = deque(maxlen=MOVING_AVG_N)
        max_rpm       = 0.0
        last_target   = 0.0
        target_start  = 0.0
        time_in_band  = None
        is_settled    = False
        tick_count    = 0

        while True:
            # ── IDLE: motor stopped ──────────────────
            if not self.state["running"]:
                self.motor.stop()
                time.sleep(0.1)
                rpm_history.clear()
                integral   = 0.0
                prev_error = 0.0
                max_rpm    = 0.0
                continue

            loop_start = time.time()
            tick_count += 1

            # ── 1. Read raw encoder speed ────────────
            pulses  = self.motor.read_and_reset_pulses()
            raw_rpm = (pulses * (1.0 / SAMPLE_TIME) * 60) / 700
            self.state["actual_rpm"] = raw_rpm

            # ── 2. Moving-average filter ─────────────
            rpm_history.append(raw_rpm)
            smoothed = sum(rpm_history) / len(rpm_history)
            self.state["smoothed_rpm"] = smoothed

            # ── 3. Reset trackers on setpoint change ─
            target = self.state["target_rpm"]
            if target != last_target:
                max_rpm      = 0.0
                last_target  = target
                target_start = time.time()
                time_in_band = None
                is_settled   = False
                self.state["settling_time"] = 0.0
                integral     = 0.0

            # ── 4. Live performance metrics ──────────
            if target > 0:
                if smoothed > max_rpm:
                    max_rpm = smoothed
                overshoot = max(0.0, (max_rpm - target) / target * 100.0)
                sse       = abs(target - smoothed) / target * 100.0
                self.state["overshoot"] = overshoot
                self.state["sse"]       = sse

                # Settling time (2% band, must stay 0.5s)
                if not is_settled:
                    lo, hi = target * (1 - SETTLING_BAND), target * (1 + SETTLING_BAND)
                    if lo <= smoothed <= hi:
                        if time_in_band is None:
                            time_in_band = time.time()
                        elif (time.time() - time_in_band) >= 0.5:
                            is_settled = True
                            self.state["settling_time"] = time_in_band - target_start
                    else:
                        time_in_band = None
                        self.state["settling_time"] = time.time() - target_start
            else:
                self.state["overshoot"]    = 0.0
                self.state["sse"]          = 0.0
                self.state["settling_time"] = 0.0

            # ── 5. Safety cutoff ─────────────────────
            from motor_driver import MAX_SAFE_RPM
            if raw_rpm > MAX_SAFE_RPM:
                self.state["running"] = False
                self.state["alarm"]   = f"SAFETY CUTOFF: {raw_rpm:.1f} RPM > {MAX_SAFE_RPM} RPM"
                logger.log_alarm("CRITICAL", self.state["alarm"])
                continue

            # Clear alarm if running fine
            self.state["alarm"] = None

            # ── 6. PID computation ───────────────────
            Kp, Ki, Kd = self.state["Kp"], self.state["Ki"], self.state["Kd"]
            error    = target - smoothed
            P_out    = Kp * error
            integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral + error * SAMPLE_TIME))
            I_out    = Ki * integral
            D_out    = Kd * ((error - prev_error) / SAMPLE_TIME)
            pwm      = max(0.0, min(MAX_PWM, P_out + I_out + D_out))

            self.state["pwm"] = pwm
            self.motor.set_pwm(pwm)
            prev_error = error

            # ── 7. Log to SQLite every 250ms ─────────
            if tick_count % DB_LOG_EVERY == 0:
                logger.log_run(target, raw_rpm, smoothed, pwm, Kp, Ki, Kd)

            # ── 8. Strict 50ms timing ────────────────
            elapsed = time.time() - loop_start
            if elapsed < SAMPLE_TIME:
                time.sleep(SAMPLE_TIME - elapsed)
