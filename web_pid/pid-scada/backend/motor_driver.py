"""
motor_driver.py
TB6612FNG motor driver abstraction using RPi.GPIO (hardware) or
a first-order simulation (mock) when running off-Pi.

Hardware:
  PWMA  → GPIO 12  (hardware PWM, 1kHz)
  AIN1  → GPIO 23  (direction)
  AIN2  → GPIO 24  (direction)
  STBY  → GPIO 25  (enable, active HIGH)
  ENC_A → GPIO 17  (quadrature A)
  ENC_B → GPIO 27  (quadrature B)
"""
import threading
import time
import math
import random

from config import (
    PWMA, AIN1, AIN2, STBY, ENC_A, ENC_B,
    PWM_FREQ, PPR, GEAR_RATIO, MAX_SAFE_RPM,
    MOCK_TAU, MOCK_GAIN, MOCK_NOISE_AMP, SAMPLE_TIME,
)

# ─────────────────────────────────────────────────────────
# Hardware availability detection
# ─────────────────────────────────────────────────────────
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    # Quick sanity: try to set a pin mode (fails gracefully off-Pi)
    GPIO.setup(PWMA, GPIO.OUT)
    HARDWARE_AVAILABLE = True
    print("✅ RPi.GPIO detected — hardware mode active.")
except Exception as e:
    GPIO = None
    HARDWARE_AVAILABLE = False
    print(f"⚠️  RPi.GPIO unavailable ({e}) — running in MOCK (simulation) mode.")


# ─────────────────────────────────────────────────────────
# Real Hardware Driver  (RPi.GPIO)
# ─────────────────────────────────────────────────────────
class HardwareMotorDriver:
    """
    Controls TB6612FNG via RPi.GPIO.
    Quadrature encoder on ENC_A/ENC_B with interrupt callbacks.
    Thread-safe encoder counter.
    """

    def __init__(self):
        self._lock       = threading.Lock()
        self._enc_count  = 0   # signed quadrature count
        self._last_a     = GPIO.LOW

        # ── Configure GPIO ────────────────────────────
        GPIO.setup(AIN1, GPIO.OUT)
        GPIO.setup(AIN2, GPIO.OUT)
        GPIO.setup(STBY, GPIO.OUT)
        GPIO.setup(ENC_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(ENC_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Hardware PWM via GPIO.PWM
        self._pwm = GPIO.PWM(PWMA, PWM_FREQ)
        self._pwm.start(0)

        # Enable driver (STBY HIGH)
        GPIO.output(STBY, GPIO.HIGH)

        # Direction: forward
        GPIO.output(AIN1, GPIO.HIGH)
        GPIO.output(AIN2, GPIO.LOW)

        # Encoder interrupts — both rising & falling on both channels
        GPIO.add_event_detect(ENC_A, GPIO.BOTH, callback=self._enc_callback)
        GPIO.add_event_detect(ENC_B, GPIO.BOTH, callback=self._enc_callback)

        print(f"✅ HardwareMotorDriver init: PWM@{PWM_FREQ}Hz, ENC A={ENC_A} B={ENC_B}")

    def _enc_callback(self, channel):
        """Quadrature decode — increments or decrements count."""
        a = GPIO.input(ENC_A)
        b = GPIO.input(ENC_B)
        with self._lock:
            # Standard quadrature state machine
            if channel == ENC_A:
                if a != b:
                    self._enc_count += 1
                else:
                    self._enc_count -= 1
            else:  # channel == ENC_B
                if a == b:
                    self._enc_count += 1
                else:
                    self._enc_count -= 1

    def read_and_reset_count(self):
        """Atomically read and zero the encoder count."""
        with self._lock:
            count = self._enc_count
            self._enc_count = 0
        return count

    def count_to_rpm(self, count: int, delta_t: float) -> float:
        """
        Convert raw quadrature counts to RPM.
        rpm = (|counts| / PPR / GR) / delta_t * 60
        PPR=7, GR=30, 4× quadrature → COUNTS_PER_REV = 840
        """
        if delta_t <= 0:
            return 0.0
        counts_per_rev = PPR * GEAR_RATIO * 4   # 840
        revolutions    = abs(count) / counts_per_rev
        rpm = (revolutions / delta_t) * 60.0
        return rpm

    def set_pwm(self, pwm_percent: float):
        """Set motor PWM duty cycle (0–100%)."""
        duty = max(0.0, min(100.0, pwm_percent))
        self._pwm.ChangeDutyCycle(duty)

    def stop(self):
        """Cut power and actively brake."""
        self._pwm.ChangeDutyCycle(0)
        GPIO.output(AIN1, GPIO.LOW)
        GPIO.output(AIN2, GPIO.LOW)

    def cleanup(self):
        """Safe shutdown — stop motor, release GPIO."""
        try:
            self.stop()
            GPIO.output(STBY, GPIO.LOW)
            self._pwm.stop()
            GPIO.cleanup()
            print("✅ GPIO cleanup complete.")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")


# ─────────────────────────────────────────────────────────
# Mock Driver  (simulation — first-order motor + noise)
# ─────────────────────────────────────────────────────────
class MockMotorDriver:
    """
    Simulates a DC motor with first-order lag + Gaussian noise.
    actual_rpm ≈ target_rpm × (1 - e^(-t/tau))
    """

    def __init__(self):
        self._simulated_rpm = 0.0
        self._pwm_percent   = 0.0
        self._lock          = threading.Lock()
        self._t             = time.time()

        # Simulation thread
        sim = threading.Thread(target=self._simulate, daemon=True)
        sim.start()
        print("🔶 MockMotorDriver started (simulation mode).")

    def _simulate(self):
        dt = 0.02   # 20ms simulation step
        while True:
            with self._lock:
                pwm     = self._pwm_percent
                current = self._simulated_rpm

            target_rpm = pwm * MOCK_GAIN
            # First-order lag: new = current + (target - current) * (dt/tau)
            new_rpm = current + (target_rpm - current) * (dt / MOCK_TAU)
            # Gaussian noise
            noise   = random.gauss(0, MOCK_NOISE_AMP)

            with self._lock:
                self._simulated_rpm = max(0.0, new_rpm + noise)

            time.sleep(dt)

    def read_and_reset_count(self):
        """Return equivalent encoder counts for SAMPLE_TIME window."""
        with self._lock:
            rpm = self._simulated_rpm
        # counts = RPM / 60 × COUNTS_PER_REV × dt
        counts_per_rev = PPR * GEAR_RATIO * 4   # 840
        counts = (rpm / 60.0) * counts_per_rev * SAMPLE_TIME
        return int(counts)

    def count_to_rpm(self, count: int, delta_t: float) -> float:
        """Convert mock count back to RPM (keeps uniform interface)."""
        if delta_t <= 0:
            return 0.0
        counts_per_rev = PPR * GEAR_RATIO * 4
        return abs(count) / counts_per_rev / delta_t * 60.0

    def set_pwm(self, pwm_percent: float):
        with self._lock:
            self._pwm_percent = max(0.0, min(100.0, pwm_percent))

    def stop(self):
        with self._lock:
            self._pwm_percent = 0.0

    def cleanup(self):
        self.stop()
        print("🔶 Mock driver cleanup.")


# ─────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────
def get_motor_driver():
    if HARDWARE_AVAILABLE:
        return HardwareMotorDriver()
    return MockMotorDriver()
