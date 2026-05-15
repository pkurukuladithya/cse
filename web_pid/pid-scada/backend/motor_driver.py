"""
motor_driver.py
Abstraction layer for the TB6612 motor driver via pigpio.
Automatically falls back to a mock driver when pigpio is unavailable (PC dev mode).
"""
import threading
import time
import math

# --- Pin Definitions ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

PULSES_PER_REV = 700
MAX_SAFE_RPM = 100

# ─────────────────────────────────────────────
# Try to import pigpio (only available on Pi)
# ─────────────────────────────────────────────
try:
    import pigpio
    _pi = pigpio.pi()
    HARDWARE_AVAILABLE = _pi.connected
except Exception:
    _pi = None
    HARDWARE_AVAILABLE = False

if not HARDWARE_AVAILABLE:
    print("⚠️  pigpio not connected — running in MOCK (simulation) mode.")


# ─────────────────────────────────────────────
# Real Hardware Driver
# ─────────────────────────────────────────────
class HardwareMotorDriver:
    def __init__(self):
        self.pulse_count = 0
        self._lock = threading.Lock()

        _pi.set_mode(PWMA, pigpio.OUTPUT)
        _pi.set_mode(AIN1, pigpio.OUTPUT)
        _pi.set_mode(AIN2, pigpio.OUTPUT)
        _pi.set_mode(ENC_A, pigpio.INPUT)
        _pi.set_pull_up_down(ENC_A, pigpio.PUD_UP)
        _pi.callback(ENC_A, pigpio.RISING_EDGE, self._count_pulse)

    def _count_pulse(self, gpio, level, tick):
        with self._lock:
            self.pulse_count += 1

    def read_and_reset_pulses(self):
        with self._lock:
            count = self.pulse_count
            self.pulse_count = 0
        return count

    def set_pwm(self, pwm_percent: float):
        pwm_val = int((max(0.0, min(100.0, pwm_percent)) / 100.0) * 255)
        _pi.write(AIN1, 1)
        _pi.write(AIN2, 0)
        _pi.set_PWM_dutycycle(PWMA, pwm_val)

    def stop(self):
        _pi.write(AIN1, 0)
        _pi.write(AIN2, 0)
        _pi.set_PWM_dutycycle(PWMA, 0)


# ─────────────────────────────────────────────
# Mock Driver (simulates a first-order motor response)
# ─────────────────────────────────────────────
class MockMotorDriver:
    """
    Simulates a DC motor with first-order lag + noise.
    actual_rpm ≈ target_rpm * (1 - e^(-t/tau))
    """
    def __init__(self):
        self._simulated_rpm = 0.0
        self._pwm_percent = 0.0
        self._lock = threading.Lock()
        # Start simulation thread
        t = threading.Thread(target=self._simulate, daemon=True)
        t.start()

    def _simulate(self):
        """Continuously update simulated RPM based on PWM."""
        TAU = 0.8  # Motor time constant (seconds)
        MOTOR_GAIN = 0.6  # RPM per % PWM at steady state
        dt = 0.05
        while True:
            with self._lock:
                pwm = self._pwm_percent
                current = self._simulated_rpm
            target_physical_rpm = pwm * MOTOR_GAIN
            # First-order lag
            new_rpm = current + (target_physical_rpm - current) * (dt / TAU)
            # Add small Gaussian noise
            noise = (hash(time.time_ns()) % 100 - 50) / 200.0
            with self._lock:
                self._simulated_rpm = max(0.0, new_rpm + noise)
            time.sleep(dt)

    def read_and_reset_pulses(self):
        """Convert simulated RPM to equivalent pulse count for 50ms window."""
        with self._lock:
            rpm = self._simulated_rpm
        # pulses = RPM / 60 * PULSES_PER_REV * sample_time
        pulses = (rpm / 60.0) * PULSES_PER_REV * 0.05
        return int(pulses)

    def set_pwm(self, pwm_percent: float):
        with self._lock:
            self._pwm_percent = max(0.0, min(100.0, pwm_percent))

    def stop(self):
        with self._lock:
            self._pwm_percent = 0.0


# ─────────────────────────────────────────────
# Factory — returns the correct driver
# ─────────────────────────────────────────────
def get_motor_driver():
    if HARDWARE_AVAILABLE:
        print("✅ Using real pigpio hardware driver.")
        return HardwareMotorDriver()
    else:
        print("🔶 Using mock simulation driver.")
        return MockMotorDriver()
