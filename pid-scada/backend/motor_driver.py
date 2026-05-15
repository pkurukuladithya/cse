import threading
import time
from typing import Callable

try:
    import RPi.GPIO as GPIO
    HARDWARE_GPIO_AVAILABLE = True
except ImportError:
    GPIO = None
    HARDWARE_GPIO_AVAILABLE = False

from config import (
    AIN1_PIN,
    AIN2_PIN,
    ENC_A_PIN,
    ENC_B_PIN,
    GEAR_RATIO,
    PPR,
    PWMA_PIN,
    STBY_PIN,
    RPM_SAMPLE_INTERVAL,
    MAX_PWM,
    MIN_PWM,
)


class MotorDriver:
    def __init__(self, use_mock: bool = False):
        self.counter = 0
        self.lock = threading.Lock()
        self.last_count = 0
        self.last_read = time.time()
        self.pwm_value = 0.0
        self._initialized = False
        self.use_mock = use_mock or not HARDWARE_GPIO_AVAILABLE
        self._sim_rpm = 0.0
        self._sim_target_rpm = 0.0
        self._sim_start = time.time()
        self._encoder_thread = None
        self._stop_encoder_thread = False
        self._last_a = 0
        self._last_b = 0

        if not self.use_mock and GPIO is None:
            raise RuntimeError("RPi.GPIO is required for hardware motor driver")

        if self.use_mock:
            self._setup_mock()
        else:
            self._setup_gpio()

    def _setup_mock(self):
        """Mock setup for development on non-Pi systems."""
        self._initialized = True
        print("[MOCK] Motor driver initialized in simulation mode")

    def _setup_gpio(self):
        """Real GPIO setup for Raspberry Pi using polling instead of event callbacks."""
        if GPIO is None:
            raise RuntimeError("GPIO not available")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PWMA_PIN, GPIO.OUT)
        GPIO.setup(AIN1_PIN, GPIO.OUT)
        GPIO.setup(AIN2_PIN, GPIO.OUT)
        GPIO.setup(STBY_PIN, GPIO.OUT)
        GPIO.setup(ENC_A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(ENC_B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.output(STBY_PIN, GPIO.LOW)
        GPIO.output(AIN1_PIN, GPIO.LOW)
        GPIO.output(AIN2_PIN, GPIO.LOW)
        self.pwm = GPIO.PWM(PWMA_PIN, 1000)
        self.pwm.start(0)

        self._stop_encoder_thread = False
        self._encoder_thread = threading.Thread(target=self._encoder_polling_loop, daemon=True)
        self._encoder_thread.start()
        self._initialized = True

    def _encoder_polling_loop(self):
        """Poll encoder pins at ~1000Hz to detect quadrature changes without event callbacks."""
        while not self._stop_encoder_thread and self._initialized:
            try:
                a = GPIO.input(ENC_A_PIN)
                b = GPIO.input(ENC_B_PIN)
                if a != self._last_a or b != self._last_b:
                    with self.lock:
                        if a != self._last_a:
                            self.counter += 1 if (a == b) else -1
                        self._last_a = a
                        self._last_b = b
                time.sleep(0.001)
            except Exception:
                break

    def set_pwm(self, duty: float):
        duty = max(MIN_PWM, min(MAX_PWM, float(duty)))
        self.pwm_value = duty
        if not self._initialized:
            return
        if self.use_mock:
            self._sim_target_rpm = (duty / 100.0) * 120.0
        else:
            self.pwm.ChangeDutyCycle(duty)
            GPIO.output(STBY_PIN, GPIO.HIGH if duty > 0 else GPIO.LOW)
            if duty > 0:
                GPIO.output(AIN1_PIN, GPIO.HIGH)
                GPIO.output(AIN2_PIN, GPIO.LOW)
            else:
                GPIO.output(AIN1_PIN, GPIO.LOW)
                GPIO.output(AIN2_PIN, GPIO.LOW)

    def stop(self):
        self.set_pwm(0.0)

    def cleanup(self):
        if not self._initialized:
            return
        self.stop()
        self._stop_encoder_thread = True
        if self._encoder_thread and self._encoder_thread.is_alive():
            self._encoder_thread.join(timeout=1.0)
        if self.use_mock:
            print("[MOCK] Motor driver cleaned up")
        else:
            self.pwm.stop()
            GPIO.cleanup()

    def read_rpm(self) -> float:
        if self.use_mock:
            return self._read_rpm_mock()
        now = time.time()
        with self.lock:
            delta = self.counter - self.last_count
            self.last_count = self.counter
        dt = max(1e-4, now - self.last_read)
        self.last_read = now
        rpm = (delta / PPR / GEAR_RATIO) / dt * 60.0
        return max(0.0, rpm)

    def _read_rpm_mock(self) -> float:
        """Simulate first-order motor response: rpm += (target_rpm - rpm) * tau * dt."""
        now = time.time()
        dt = max(1e-4, now - self.last_read)
        self.last_read = now
        tau = 0.5
        self._sim_rpm += (self._sim_target_rpm - self._sim_rpm) * (dt / tau)
        self._sim_rpm = max(0.0, min(120.0, self._sim_rpm))
        return self._sim_rpm

