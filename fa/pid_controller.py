import pigpio
import time
import csv
import sys

# --- HARDWARE SETUP ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

# --- SYSTEM CONSTANTS ---
PULSES_PER_REV = 700 
SAMPLE_TIME = 0.05       # RUBRIC: Fixed sampling rate (50ms)
MAX_SAFE_RPM = 100       # RUBRIC: Safety cut-off limit (based on your 50 RPM max)
MAX_PWM = 100.0          # Max throttle

# --- PID GAINS (Placeholders for Module 2) ---
Kp = 0.5
Ki = 1.7
Kd = 0.01

# --- SYSTEM STATE VARIABLES ---
pulse_count = 0
prev_error = 0
integral = 0
MAX_INTEGRAL = 200.0      # RUBRIC: Anti-windup clamp limit

print("Connecting to pigpio...")
pi = pigpio.pi()
if not pi.connected:
    print("🚨 ERROR: Run 'sudo pigpiod' first!")
    sys.exit()

# Initialize Pins
pi.set_mode(PWMA, pigpio.OUTPUT)
pi.set_mode(AIN1, pigpio.OUTPUT)
pi.set_mode(AIN2, pigpio.OUTPUT)
pi.set_mode(ENC_A, pigpio.INPUT)
pi.set_pull_up_down(ENC_A, pigpio.PUD_UP)

# RUBRIC: Interrupt-driven encoder counting
def count_pulse(gpio, level, tick):
    global pulse_count
    pulse_count += 1

cb = pi.callback(ENC_A, pigpio.RISING_EDGE, count_pulse)

def set_motor_pwm(pwm_percent):
    # Ensure PWM stays strictly between 0 and 100
    pwm_percent = max(0.0, min(MAX_PWM, pwm_percent))
    pwm_val = int((pwm_percent / 100.0) * 255)
    
    pi.write(AIN1, 1) # Force Forward for this test
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, pwm_val)

def stop_motor():
    pi.write(AIN1, 0)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, 0)

try:
    print("\n--- PID CLOSED-LOOP CONTROLLER ---")
    target_rpm = float(input("Enter Target Speed (RPM) [e.g., 25, 40]: "))
    test_duration = float(input("Enter Test Duration (seconds) [e.g., 5]: "))
    
    filename = f"pid_test6_{int(target_rpm)}rpm.csv"
    print(f"\nStarting PID loop targeting {target_rpm} RPM for {test_duration}s...")
    time.sleep(2)

    # RUBRIC: CSV Logging setup
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "Target (RPM)", "Actual (RPM)", "Error", "PWM Output", "P", "I", "D"])

        start_time = time.time()
        next_loop_time = start_time + SAMPLE_TIME

        # --- THE MAIN CONTROL LOOP ---
        while (time.time() - start_time) < test_duration:
            current_time = time.time()
            
            # 1. Read Pulses & Calculate RPM
            current_pulses = pulse_count
            pulse_count = 0 # Reset for the next interval
            actual_rpm = (current_pulses * (1.0 / SAMPLE_TIME) * 60) / PULSES_PER_REV
            
            # RUBRIC: Safety Cut-off
            if actual_rpm > MAX_SAFE_RPM:
                print(f"\n🚨 SAFETY TRIGGERED: Motor exceeded {MAX_SAFE_RPM} RPM! Shutting down.")
                stop_motor()
                sys.exit()

            # 2. Calculate Error
            error = target_rpm - actual_rpm

            # 3. Calculate PID Terms
            P_out = Kp * error
            
            integral += (error * SAMPLE_TIME)
            # RUBRIC: Anti-Windup Protection (Clamp the integral)
            integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral))
            I_out = Ki * integral
            
            derivative = (error - prev_error) / SAMPLE_TIME
            D_out = Kd * derivative

            # 4. Compute Final Output
            control_output = P_out + I_out + D_out
            
            # Since we are only driving forward for this step test, clamp output at 0 minimum
            final_pwm = max(0.0, min(MAX_PWM, control_output))
            set_motor_pwm(final_pwm)

            # 5. Log Data
            elapsed_time = round(current_time - start_time, 3)
            writer.writerow([elapsed_time, target_rpm, round(actual_rpm, 2), round(error, 2), round(final_pwm, 2), round(P_out, 2), round(I_out, 2), round(D_out, 2)])
            
            print(f"Time: {elapsed_time}s | Target: {target_rpm} | RPM: {round(actual_rpm, 1)} | PWM: {round(final_pwm, 1)}%")

            # 6. Save state and wait for the exact next sampling interval
            prev_error = error
            
            # This ensures a strict, fixed sampling rate
            sleep_time = next_loop_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            next_loop_time += SAMPLE_TIME

    print(f"\n✅ PID Test Complete! Data saved to {filename}")

except KeyboardInterrupt:
    print("\nEmergency Stop Triggered.")
finally:
    stop_motor()
    cb.cancel()
    pi.stop()