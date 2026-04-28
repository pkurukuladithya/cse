import pigpio
import time
import csv
import sys

# --- HARDWARE SETUP ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

# --- MOTOR SPECS (Adjust if your RPM looks wrong) ---
# Example: 7 pulses per motor shaft rev * 100:1 gear ratio = 700 PPR
PULSES_PER_REVOLUTION = 700 
SAMPLE_TIME = 0.05  # Log data every 50 milliseconds
TEST_DURATION = 2.0 # Total test time in seconds (N20s spool up fast!)

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

pulse_count = 0

def count_pulse(gpio, level, tick):
    global pulse_count
    pulse_count += 1

cb = pi.callback(ENC_A, pigpio.RISING_EDGE, count_pulse)

def set_motor_pwm(pwm_percent):
    pwm_val = int((pwm_percent / 100.0) * 255)
    pi.write(AIN1, 1) # Forward
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, pwm_val)

def stop_motor():
    pi.write(AIN1, 0)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, 0)

try:
    # 1. Ask the user for the test parameters
    print("\n--- OPEN LOOP STEP RESPONSE TEST ---")
    target_pwm = float(input("Enter Test PWM % (e.g., 40, 60, 80): "))
    filename = f"open_loop_{int(target_pwm)}pct.csv"
    
    print(f"\nMotor will run at {target_pwm}% for {TEST_DURATION} seconds.")
    print("Keep hands clear! Starting in 3 seconds...")
    time.sleep(3)

    # 2. Prepare the CSV File
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time (s)", "PWM (%)", "Speed (RPM)"])

        # 3. BLAST THE MOTOR (The "Step" Input)
        start_time = time.time()
        set_motor_pwm(target_pwm)

        # 4. The High-Speed Logging Loop
        while (time.time() - start_time) < TEST_DURATION:
            loop_start = time.time()
            
            # Reset pulse count, wait 50ms, then check how many pulses happened
            pulse_count = 0
            time.sleep(SAMPLE_TIME)
            current_pulses = pulse_count
            
            # Calculate RPM: (Pulses in 50ms * 20 = Pulses per sec) * 60 = Pulses per min
            rpm = (current_pulses * (1.0 / SAMPLE_TIME) * 60) / PULSES_PER_REVOLUTION
            current_time = round(time.time() - start_time, 3)

            # Write to CSV and print to terminal
            writer.writerow([current_time, target_pwm, round(rpm, 2)])
            print(f"Time: {current_time}s | PWM: {target_pwm}% | RPM: {round(rpm, 2)}")

    print(f"\n✅ Test Complete! Data saved to {filename}")

except KeyboardInterrupt:
    print("\nEmergency Stop Triggered.")
finally:
    stop_motor()
    cb.cancel()
    pi.stop()