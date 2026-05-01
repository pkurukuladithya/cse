import pigpio
import time
import csv

# --- HARDWARE SETUP ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

PULSES_PER_REV = 700 
SAMPLE_TIME = 0.05
MAX_PWM = 100.0

pi = pigpio.pi()
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
    pi.write(AIN1, 1)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, pwm_val)

# --- THE STAIRCASE PROFILE ---
# Format: (Target RPM, Duration in Seconds)
sequence = [(20, 4.0), (40, 4.0), (15, 4.0), (30, 4.0), (0, 2.0)]

Kp = 0.5
Ki = 1.7
Kd = 0.01
MAX_INTEGRAL = 200.0

integral = 0
prev_error = 0
data_log = []
start_time = time.time()
step_id = 1 # NEW: Track which step we are on

print("🚀 Starting Automated Multi-Setpoint Test...")

try:
    for target_rpm, duration in sequence:
        print(f"➡️ Step {step_id}: Target {target_rpm} RPM for {duration} seconds...")
        step_start = time.time()
        
        while (time.time() - step_start) < duration:
            loop_start = time.time()
            
            # 1. Read Speed
            current_pulses = pulse_count
            pulse_count = 0
            actual_rpm = (current_pulses * (1.0 / SAMPLE_TIME) * 60) / PULSES_PER_REV
            
            # 2. PID Math
            error = target_rpm - actual_rpm
            P_out = Kp * error
            integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral + (error * SAMPLE_TIME)))
            I_out = Ki * integral
            D_out = Kd * ((error - prev_error) / SAMPLE_TIME)
            
            # 3. Apply Power
            pwm = max(0.0, min(MAX_PWM, P_out + I_out + D_out))
            set_motor_pwm(pwm)
            prev_error = error
            
            # Log Data (Now includes step_id)
            current_time = time.time() - start_time
            data_log.append([current_time, target_rpm, actual_rpm, pwm, step_id])
            
            # Strict Timing
            elapsed = time.time() - loop_start
            if elapsed < SAMPLE_TIME:
                time.sleep(SAMPLE_TIME - elapsed)
        
        step_id += 1 # Increment for the next loop

finally:
    # Safely stop motor
    set_motor_pwm(0)
    print("🛑 Test Complete. Saving data...")
    
    # Save to CSV
    with open('multi_step_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Time (s)', 'Target (RPM)', 'Actual (RPM)', 'PWM (%)', 'Step_ID'])
        writer.writerows(data_log)
    print("✅ Saved as 'multi_step_data.csv'")