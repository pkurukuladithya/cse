"""
config.py
Central configuration — GPIO pins, motor constants, PID defaults.
Import from any module instead of repeating magic numbers.
"""

# ── GPIO Pin Map (BCM numbering) ──────────────────────────
PWMA  = 12   # Hardware PWM — motor speed
AIN1  = 23   # Motor direction A
AIN2  = 24   # Motor direction B
STBY  = 25   # Driver standby — pull HIGH to enable
ENC_A = 17   # Encoder channel A
ENC_B = 27   # Encoder channel B

# ── Motor / Encoder Constants ─────────────────────────────
PWM_FREQ      = 1000   # Hz  — hardware PWM frequency
PPR           = 7      # Pulses per revolution (pre-gearbox)
GEAR_RATIO    = 30     # Gearbox ratio
COUNTS_PER_REV = PPR * GEAR_RATIO * 4  # 4× for quadrature (A+B, both edges)

# ── Safety ────────────────────────────────────────────────
MAX_SAFE_RPM  = 120.0  # Emergency cut-off above this speed
MAX_PWM       = 100.0  # Max duty cycle (%)
MIN_PWM       = 0.0    # Min duty cycle (%)

# ── PID Defaults ──────────────────────────────────────────
DEFAULT_KP    = 1.5
DEFAULT_KI    = 1.5
DEFAULT_KD    = 0.01
DEFAULT_SP    = 60.0   # RPM setpoint

# ── PID Loop ──────────────────────────────────────────────
SAMPLE_TIME   = 0.05   # 50ms control loop period
MAX_INTEGRAL  = 200.0  # Anti-windup clamp
SETTLING_BAND = 0.02   # ±2% band for settling-time detection
SETTLE_CONFIRM = 0.5   # seconds in-band before declared settled

# ── Auto-Tuner ────────────────────────────────────────────
AT_RELAY_HIGH     = 80.0   # PWM% for relay HIGH
AT_RELAY_LOW      = 0.0    # PWM% for relay LOW
AT_DEFAULT_AMP    = 20.0   # Default relay amplitude (PWM%)
AT_MIN_CYCLES     = 4      # Minimum full oscillation cycles
AT_TIMEOUT        = 60.0   # Abort if no oscillation in 60s
AT_HYSTERESIS     = 1.0    # ±RPM hysteresis around setpoint

# ── WebSocket ─────────────────────────────────────────────
WS_TELEMETRY_INTERVAL = 0.05   # 50ms → 20Hz broadcasts

# ── Database ──────────────────────────────────────────────
import os
DB_PATH = os.path.join(os.path.dirname(__file__), "scada.db")

# ── Simulation (mock driver) ──────────────────────────────
MOCK_TAU        = 0.8    # Motor time constant (s)
MOCK_GAIN       = 0.65   # RPM per % PWM
MOCK_NOISE_AMP  = 0.3    # Gaussian noise amplitude (RPM)
