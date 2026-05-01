import pigpio
import time
import threading
from collections import deque
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- HARDWARE SETUP ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

PULSES_PER_REV = 700 
SAMPLE_TIME = 0.05
MAX_SAFE_RPM = 100
MAX_PWM = 100.0

pi = pigpio.pi()
if not pi.connected:
    print("🚨 ERROR: Run 'sudo pigpiod' first!")
    exit()

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

# --- GLOBAL STATE & REAL-TIME METRICS ---
state = {
    "target_rpm": 0.0,
    "actual_rpm": 0.0,
    "smoothed_rpm": 0.0,
    "pwm": 0.0,
    "overshoot": 0.0,
    "sse": 0.0,
    "settling_time": 0.0, 
    "Kp": 1.5,
    "Ki": 1.5,
    "Kd": 0.00,
    "running": False 
}

def set_motor_pwm(pwm_percent):
    pwm_val = int((pwm_percent / 100.0) * 255)
    pi.write(AIN1, 1)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, pwm_val)

def stop_motor():
    pi.write(AIN1, 0)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, 0)

# --- THE BACKGROUND HARDWARE THREAD ---
def pid_loop():
    global pulse_count
    integral = 0
    prev_error = 0
    MAX_INTEGRAL = 200.0
    
    # Signal Processing Buffers
    rpm_history = deque(maxlen=7) # 7-point moving average filter
    max_rpm_this_step = 0.0
    last_target = 0.0

    # Settling Time Tracking Variables
    target_start_time = 0.0
    time_entered_band = None
    is_settled = False
    settling_band = 0.02 # +/- 2% Band

    while True:
        if not state["running"]:
            stop_motor()
            time.sleep(0.1)
            rpm_history.clear()
            max_rpm_this_step = 0.0
            continue

        start_time = time.time()
        
        # 1. Read Raw Speed
        current_pulses = pulse_count
        pulse_count = 0
        raw_rpm = (current_pulses * (1.0 / SAMPLE_TIME) * 60) / PULSES_PER_REV
        state["actual_rpm"] = raw_rpm

        # 2. Live Signal Filtering (Moving Average)
        rpm_history.append(raw_rpm)
        smoothed_rpm = sum(rpm_history) / len(rpm_history)
        state["smoothed_rpm"] = smoothed_rpm

        # Reset all trackers if user changes the target slider
        if state["target_rpm"] != last_target:
            max_rpm_this_step = 0.0
            last_target = state["target_rpm"]
            target_start_time = time.time() # Start the clock!
            time_entered_band = None
            is_settled = False
            state["settling_time"] = 0.0

        # Calculate Live Metrics (Safeguard against divide by zero)
        if state["target_rpm"] > 0:
            # Overshoot & SSE Math
            if smoothed_rpm > max_rpm_this_step:
                max_rpm_this_step = smoothed_rpm
            
            overshoot_val = ((max_rpm_this_step - state["target_rpm"]) / state["target_rpm"]) * 100.0
            state["overshoot"] = max(0.0, overshoot_val)
            state["sse"] = (abs(state["target_rpm"] - smoothed_rpm) / state["target_rpm"]) * 100.0

            # LIVE SETTLING TIME MATH
            if not is_settled:
                # Calculate the 2% boundaries
                lower_bound = state["target_rpm"] * (1.0 - settling_band)
                upper_bound = state["target_rpm"] * (1.0 + settling_band)
                
                # Check if we are inside the band
                if lower_bound <= smoothed_rpm <= upper_bound:
                    if time_entered_band is None:
                        # We just entered the band. Start counting the dwell time.
                        time_entered_band = time.time()
                    elif (time.time() - time_entered_band) >= 0.5:
                        # We stayed in the band for 0.5s straight! We are officially settled.
                        is_settled = True
                        # Settling time is when we FIRST entered the band
                        state["settling_time"] = time_entered_band - target_start_time
                else:
                    # We fell out of the band. Reset the counter.
                    time_entered_band = None
                    # Update a "live" running timer so the UI shows it searching
                    state["settling_time"] = time.time() - target_start_time
        else:
            state["overshoot"] = 0.0
            state["sse"] = 0.0
            state["settling_time"] = 0.0

        # Safety Cutoff
        if raw_rpm > MAX_SAFE_RPM:
            state["running"] = False
            continue

        # 3. PID Math (Running on the smoothed data for better stability)
        error = state["target_rpm"] - smoothed_rpm
        P_out = state["Kp"] * error
        integral = max(-MAX_INTEGRAL, min(MAX_INTEGRAL, integral + (error * SAMPLE_TIME)))
        I_out = state["Ki"] * integral
        D_out = state["Kd"] * ((error - prev_error) / SAMPLE_TIME)

        # 4. Apply Power
        state["pwm"] = max(0.0, min(MAX_PWM, P_out + I_out + D_out))
        set_motor_pwm(state["pwm"])
        
        prev_error = error

        # 5. Strict Timing Wait (50ms Loop)
        elapsed = time.time() - start_time
        if elapsed < SAMPLE_TIME:
            time.sleep(SAMPLE_TIME - elapsed)

# Start the background hardware thread
threading.Thread(target=pid_loop, daemon=True).start()

# --- FLASK WEB ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    return jsonify(state)

@app.route('/api/update', methods=['POST'])
def update_params():
    data = request.json
    state["target_rpm"] = float(data.get("target_rpm", state["target_rpm"]))
    state["Kp"] = float(data.get("Kp", state["Kp"]))
    state["Ki"] = float(data.get("Ki", state["Ki"]))
    state["Kd"] = float(data.get("Kd", state["Kd"]))
    state["running"] = data.get("running", state["running"])
    return jsonify({"status": "success"})

if __name__ == '__main__':
    # Run server accessible from your laptop
    app.run(host='0.0.0.0', port=5000, debug=False)