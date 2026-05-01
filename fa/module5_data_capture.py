import pigpio
import time
import csv
import sys

# --- HARDWARE SETUP ---
PWMA, AIN1, AIN2, ENC_A = 12, 24, 23, 17
PULSES_PER_REV = 700 
SAMPLE_TIME = 0.05
TARGET_RPM = 30.0
TEST_DURATION = 5.0 # Seconds

# Module 5 Specific Gains provided by user
KP, KI, KD = 0.5, 1.7, 0.01
MAX_INTEGRAL, MAX_PWM = 200.0, 100.0

# Pigpio Setup
pi = pigpio.pi()
if not pi.connected:
    print("🚨 ERROR: pigpiod not running!")
    sys.exit()

pi.set_mode(PWMA, pigpio.OUTPUT)
pi.set_mode(AIN1, pigpio.OUTPUT)
pi.set_mode(AIN2, pigpio.OUTPUT)
pi.set_mode(ENC_A, pigpio.INPUT)
pi.set_pull_up_down(ENC_A, pigpio.PUD_UP)

pulse_count = 0
def count_pulse(gpio, level, tick):
    global pulse_count
    pulse_count += 1
pi.callback(ENC_A, pigpio.RISING_EDGE, count_pulse)

def set_motor_pwm(pwm_percent):
    pwm_val = int((pwm_percent / 100.0) * 255)
    pi.write(AIN1, 1); pi.write(AIN2, 0); pi.set_PWM_dutycycle(PWMA, pwm_val)

# --- THE PID LOOP ---
print(f"🚀 Capturing Hardware Data (Module 5 Gains)...")
integral, prev_error = 0, 0
data_log = []
start_time = time.time()

try:
    while (time.time() - start_time) < TEST_DURATION:
        loop_start = time.time()
        
        # 1. Read Raw Speed
        current_pulses = pulse_count
        pulse_count = 0
        actual_rpm = (current_pulses * (1.0 / SAMPLE_TIME) * 60) / PULSES_PER_REV
        
        # 2. PID Math
        error = TARGET_RPM - actual_rpm
        P_out = KP * error
        integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral + (error * SAMPLE_TIME)))
        I_out = KI * integral
        D_out = KD * ((error - prev_error) / SAMPLE_TIME)
        
        # 3. Apply Power
        pwm = max(0.0, min(MAX_PWM, P_out + I_out + D_out))
        set_motor_pwm(pwm)
        
        prev_error = error
        
        # Log Data
        timestamp = time.time() - start_time
        data_log.append([timestamp, TARGET_RPM, actual_rpm])
        
        # Strict Timing Wait (50ms Loop)
        elapsed = time.time() - loop_start
        if elapsed < SAMPLE_TIME:
            time.sleep(SAMPLE_TIME - elapsed)

finally:
    pi.write(AIN1, 0); pi.write(AIN2, 0); pi.set_PWM_dutycycle(PWMA, 0)
    
    # Save to dedicated CSV
    with open('module5_hardware.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (s)', 'Target (RPM)', 'Actual (RPM)'])
        writer.writerows(data_log)
    print("✅ Hardware data saved as 'module5_hardware.csv'")