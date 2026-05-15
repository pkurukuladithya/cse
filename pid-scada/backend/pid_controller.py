import time
from typing import Optional

from config import DEFAULT_SAMPLE_TIME, MAX_PWM, MIN_PWM


class PIDController:
    def __init__(self, kp: float = 1.0, ki: float = 1.5, kd: float = 0.01, setpoint: float = 60.0, sample_time: float = DEFAULT_SAMPLE_TIME):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.sample_time = sample_time

        self.last_error = 0.0
        self.integral = 0.0
        self.last_pv = 0.0
        self.output = 0.0
        self.last_time = time.time()

        self._rise_time: Optional[float] = None
        self._settle_time: Optional[float] = None
        self._overshoot_pct: Optional[float] = None
        self._itae: float = 0.0
        self._first_cross_time: Optional[float] = None
        self._max_pv: float = 0.0
        self._settle_start: Optional[float] = None

    def update_gains(self, kp: float, ki: float, kd: float):
        if self.output is not None:
            self._restore_bumpless(kp, ki, kd)
        self.kp, self.ki, self.kd = kp, ki, kd

    def _restore_bumpless(self, kp: float, ki: float, kd: float):
        error = self.setpoint - self.last_pv
        proportional = kp * error
        derivative = -kd * ((self.last_pv - self.last_pv) / self.sample_time)
        self.integral = max(min(self.output - proportional - derivative, 1000.0), -1000.0)

    def reset(self):
        self.last_error = 0.0
        self.integral = 0.0
        self.last_pv = 0.0
        self.output = 0.0
        self.last_time = time.time()
        self._rise_time = None
        self._settle_time = None
        self._overshoot_pct = None
        self._itae = 0.0
        self._first_cross_time = None
        self._max_pv = 0.0
        self._settle_start = None

    def compute(self, pv: float, timestamp: Optional[float] = None) -> float:
        now = timestamp if timestamp is not None else time.time()
        dt = now - self.last_time
        if dt < self.sample_time:
            return self.output

        error = self.setpoint - pv
        derivative = 0.0
        if dt > 0:
            derivative = -(pv - self.last_pv) / dt

        self.integral += error * dt

        unclamped = self.kp * error + self.ki * self.integral + self.kd * derivative
        clamped = max(MIN_PWM, min(MAX_PWM, unclamped))

        if clamped != unclamped:
            self.integral -= error * dt
            self.integral = max(-1000.0, min(1000.0, self.integral))

        self.output = clamped
        previous_time = self.last_time
        self.last_time = now
        self.last_error = error
        self.last_pv = pv

        self._update_performance(pv, now, now - previous_time)
        return self.output

    def _update_performance(self, pv: float, now: float, dt: float):
        if self._first_cross_time is None and pv >= self.setpoint * 0.1:
            self._first_cross_time = now
        if self._first_cross_time is not None and self._rise_time is None and pv >= self.setpoint * 0.9:
            self._rise_time = now - self._first_cross_time

        self._max_pv = max(self._max_pv, pv)
        if self.setpoint > 0:
            self._overshoot_pct = max(0.0, (self._max_pv - self.setpoint) / self.setpoint * 100.0)

        error_abs = abs(self.setpoint - pv)
        self._itae += now * error_abs * dt

        if self._settle_start is None and error_abs <= self.setpoint * 0.02:
            self._settle_start = now
        elif self._settle_start is not None and error_abs > self.setpoint * 0.02:
            self._settle_start = None
        elif self._settle_start is not None and self._settle_time is None:
            self._settle_time = now - self._settle_start

    @property
    def rise_time(self) -> Optional[float]:
        return self._rise_time

    @property
    def overshoot_pct(self) -> Optional[float]:
        return self._overshoot_pct

    @property
    def settle_time(self) -> Optional[float]:
        return self._settle_time

    @property
    def itae(self) -> float:
        return self._itae
