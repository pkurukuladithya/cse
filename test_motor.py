import pigpio
import time
import sys

# Pin Mapping from your schematic
PWMA = 12
AIN1 = 24
AIN2 = 23

print("Connecting to pigpio daemon...")
pi = pigpio.pi()

if not pi.connected:
    print("🚨 ERROR: Could not connect to pigpio daemon.")
    print("Run 'sudo pigpiod' in the terminal first!")
    sys.exit()

# Setup GPIO pins as outputs
pi.set_mode(PWMA, pigpio.OUTPUT)
pi.set_mode(AIN1, pigpio.OUTPUT)
pi.set_mode(AIN2, pigpio.OUTPUT)

def set_motor(speed_percent, direction):
    # pigpio uses a 0-255 scale for PWM, so we convert the 0-100%
    pwm_val = int((speed_percent / 100.0) * 255)
    
    if direction == "forward":
        pi.write(AIN1, 1)
        pi.write(AIN2, 0)
    elif direction == "reverse":
        pi.write(AIN1, 0)
        pi.write(AIN2, 1)
        
    pi.set_PWM_dutycycle(PWMA, pwm_val)

def stop_motor():
    pi.write(AIN1, 0)
    pi.write(AIN2, 0)
    pi.set_PWM_dutycycle(PWMA, 0)

try:
    print("Testing Motor Forward at 50% Speed...")
    set_motor(50, "forward")
    time.sleep(3) # Run for 3 seconds
    
    print("Stopping Motor...")
    stop_motor()
    time.sleep(1)
    
    print("Testing Motor Reverse at 50% Speed...")
    set_motor(50, "reverse")
    time.sleep(3)
    
    print("Test Complete. Stopping.")

except KeyboardInterrupt:
    print("\nTest forcefully stopped by user.")
finally:
    # Safe cleanup without the RPi.GPIO bug!
    stop_motor()
    pi.stop()
    print("Cleaned up safely.")