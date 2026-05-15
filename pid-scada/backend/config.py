from dataclasses import dataclass

# GPIO pin configuration in BCM mode
PWMA_PIN = 12
AIN1_PIN = 23
AIN2_PIN = 24
STBY_PIN = 25
ENC_A_PIN = 17
ENC_B_PIN = 27

# Motor encoder calibration
PPR = 7
GEAR_RATIO = 30.0
RPM_SAMPLE_INTERVAL = 0.05

# PID defaults
DEFAULT_KP = 1.0
DEFAULT_KI = 1.5
DEFAULT_KD = 0.01
DEFAULT_SETPOINT = 60.0
DEFAULT_SAMPLE_TIME = 0.05

# Auto-tuner settings
AUTOTUNE_DURATION = 15.0
AUTOTUNE_PROGRESS_INTERVAL = 0.5

# SQLite database
DATABASE_FILE = "pid_scada.db"

# Safety limits
MAX_PWM = 100.0
MIN_PWM = 0.0
MAX_RPM = 130.0
MIN_RPM = 0.0

# WebSocket update interval (seconds)
TELEMETRY_INTERVAL = 0.05
