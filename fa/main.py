import pigpio
import time
import csv
import sys
import numpy as np

# --- HARDWARE SETUP ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

PULSES_PER_REV = 700 
SAMPLE_TIME = 0.05
MAX_SAFE_RPM = 100
MAX_PWM = 100.0

# --- FINAL OPTIMAL PID GAINS ---
Kp = 1.5
Ki = 1.5
Kd = 0.0
MAX_INTEGRAL = 200.0

print("Connecting to hardware...")
pi = pigpio.pi()
if not pi.connected:
    print("🚨 ERROR: Run 'sudo pigpiod' first!")
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
cb = pi.callback(ENC_A, pigpio.RISING_EDGE, count_pulse)

def set_motor_pwm(pwm_percent):
    pwm_percent = max(0.0, min(MAX_PWM, pwm_percent))
    pwm_val = int((pwm_percent / 100.0) * 255)
    pi.write(AIN1, 1)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, pwm_val)

def stop_motor():
    pi.write(AIN1, 0)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, 0)

# --- MODULE 1: OPEN LOOP TEST ---
def run_open_loop():
    global pulse_count
    target_pwm = float(input("\nEnter Target PWM % (e.g., 60): "))
    duration = 3.0
    filename = f"final_openloop_{int(target_pwm)}pct.csv"
    
    print(f"\nRunning Open Loop at {target_pwm}% for {duration}s...")
    time.sleep(2)
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "PWM (%)", "Speed (RPM)"])
        
        start_time = time.time()
        set_motor_pwm(target_pwm)
        
        while (time.time() - start_time) < duration:
            pulse_count = 0
            time.sleep(SAMPLE_TIME)
            rpm = (pulse_count * (1.0 / SAMPLE_TIME) * 60) / PULSES_PER_REV
            writer.writerow([round(time.time() - start_time, 3), target_pwm, round(rpm, 2)])
            
    stop_motor()
    print(f"✅ Open Loop Test saved to {filename}")

# --- MODULE 2-5: PID CLOSED LOOP & JITTER TEST ---
def run_pid_loop():
    global pulse_count
    target_rpm = float(input("\nEnter Target RPM (e.g., 20, 30, 40): "))
    duration = float(input("Enter Test Duration in seconds (e.g., 5, 15): "))
    filename = f"final_pid_{int(target_rpm)}rpm.csv"
    
    print(f"\nRunning PID Control at {target_rpm} RPM for {duration}s...")
    time.sleep(2)
    
    integral = 0
    prev_error = 0
    jitter_log = [] # Array to track CPU timing errors
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "Target (RPM)", "Actual (RPM)", "PWM Output", "Loop Time (s)"])
        
        start_time = time.time()
        next_loop_time = start_time + SAMPLE_TIME
        last_exec_time = start_time
        
        while (time.time() - start_time) < duration:
            current_time = time.time()
            
            # CPU JITTER CALCULATION
            actual_dt = current_time - last_exec_time
            jitter_log.append(actual_dt)
            last_exec_time = current_time
            
            current_pulses = pulse_count
            pulse_count = 0 
            actual_rpm = (current_pulses * (1.0 / actual_dt) * 60) / PULSES_PER_REV
            
            if actual_rpm > MAX_SAFE_RPM:
                stop_motor()
                print(f"\n🚨 SAFETY TRIGGERED: Exceeded {MAX_SAFE_RPM} RPM!")
                return

            error = target_rpm - actual_rpm
            P_out = Kp * error
            integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral + (error * actual_dt)))
            I_out = Ki * integral
            D_out = Kd * ((error - prev_error) / actual_dt)
            
            final_pwm = max(0.0, min(MAX_PWM, P_out + I_out + D_out))
            set_motor_pwm(final_pwm)
            
            writer.writerow([round(current_time - start_time, 3), target_rpm, round(actual_rpm, 2), round(final_pwm, 2), round(actual_dt, 4)])
            prev_error = error
            
            sleep_time = next_loop_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            next_loop_time += SAMPLE_TIME
            
    stop_motor()
    print(f"✅ PID Test saved to {filename}")
    
    # --- CALCULATE AND PRINT JITTER METRICS ---
    avg_loop = np.mean(jitter_log)
    max_loop = np.max(jitter_log)
    jitter_ms = (max_loop - SAMPLE_TIME) * 1000
    print("\n--- 🖥️ MODULE 5: CPU PERFORMANCE METRICS ---")
    print(f"Target Loop Time: {SAMPLE_TIME} seconds (50ms)")
    print(f"Average Loop Time: {avg_loop:.4f} seconds")
    print(f"Maximum Loop Time: {max_loop:.4f} seconds")
    print(f"MAX JITTER: {jitter_ms:.2f} milliseconds")
    print("-------------------------------------------\n")

# --- MAIN MENU UI ---
try:
    while True:
        print("\n" + "="*40)
        print("  CSE3034 INDUSTRIAL MOTOR CONTROLLER  ")
        print("="*40)
        print("1. Run Open-Loop Step Test (Module 1)")
        print("2. Run Closed-Loop PID Test (Modules 2-5)")
        print("3. Exit System")
        choice = input("\nSelect an option (1-3): ")
        
        if choice == '1':
            run_open_loop()
        elif choice == '2':
            run_pid_loop()
        elif choice == '3':
            print("Shutting down safely...")
            break
        else:
            print("Invalid choice. Try again.")
except KeyboardInterrupt:
    print("\nEmergency Stop Triggered.")
finally:
    stop_motor()
    cb.cancel()
    pi.stop()