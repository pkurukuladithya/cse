from flask import Flask, render_template, request, jsonify
import pigpio
import sys

app = Flask(__name__)

# --- HARDWARE SETUP ---
PWMA = 12
AIN1 = 24
AIN2 = 23
ENC_A = 17

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

# Global variables for state
current_speed = 0
current_direction = "stop"
pulse_count = 0

# Encoder Interrupt Function
def count_pulse(gpio, level, tick):
    global pulse_count
    pulse_count += 1

cb = pi.callback(ENC_A, pigpio.RISING_EDGE, count_pulse)

def apply_motor_state():
    # Convert 0-100% to pigpio's 0-255 PWM range
    pwm_val = int((current_speed / 100.0) * 255)
    
    if current_direction == "forward":
        pi.write(AIN1, 1)
        pi.write(AIN2, 0)
        pi.set_PWM_dutycycle(PWMA, pwm_val)
    elif current_direction == "reverse":
        pi.write(AIN1, 0)
        pi.write(AIN2, 1)
        pi.set_PWM_dutycycle(PWMA, pwm_val)
    else: # Stop
        pi.write(AIN1, 0)
        pi.write(AIN2, 0)
        pi.set_PWM_dutycycle(PWMA, 0)

# --- WEB ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/control', methods=['POST'])
def control():
    global current_speed, current_direction, pulse_count
    data = request.json
    
    if 'direction' in data:
        current_direction = data['direction']
    if 'speed' in data:
        current_speed = int(data['speed'])
    if 'reset_encoder' in data:
        pulse_count = 0

    apply_motor_state()
    return jsonify({"status": "success"})

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "speed": current_speed,
        "direction": current_direction,
        "pulses": pulse_count
    })

if __name__ == '__main__':
    try:
        # Run the server on all network interfaces
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        pi.write(AIN1, 0)
        pi.write(AIN2, 0)
        pi.set_PWM_dutycycle(PWMA, 0)
        cb.cancel()
        pi.stop()