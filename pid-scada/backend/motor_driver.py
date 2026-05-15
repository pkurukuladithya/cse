import threading
import time
from typing import Callable

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

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
    def __init__(self):
        self.counter = 0
        self.lock = threading.Lock()
        self.last_count = 0
        self.last_read = time.time()
        self.pwm_value = 0.0
        self._initialized = False

        if GPIO is None:
            raise RuntimeError("RPi.GPIO is required for motor driver")

        self._setup_gpio()

    def _setup_gpio(self):
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

        GPIO.add_event_detect(ENC_A_PIN, GPIO.BOTH, callback=self._encoder_callback)
        GPIO.add_event_detect(ENC_B_PIN, GPIO.BOTH, callback=self._encoder_callback)
        self._initialized = True

    def _encoder_callback(self, channel: int):
        with self.lock:
            a = GPIO.input(ENC_A_PIN)
            b = GPIO.input(ENC_B_PIN)
            if a == b:
                self.counter += 1
            else:
                self.counter -= 1

    def set_pwm(self, duty: float):
        duty = max(MIN_PWM, min(MAX_PWM, float(duty)))
        self.pwm_value = duty
        if self._initialized:
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
        self.pwm.stop()
        GPIO.cleanup()

    def read_rpm(self) -> float:
        now = time.time()
        with self.lock:
            delta = self.counter - self.last_count
            self.last_count = self.counter
        dt = max(1e-4, now - self.last_read)
        self.last_read = now
        rpm = (delta / PPR / GEAR_RATIO) / dt * 60.0
        return max(0.0, rpm)

