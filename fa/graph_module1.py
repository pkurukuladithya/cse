import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Load the real CSV data
filename = "open_loop_60pct.csv"
try:
    data = pd.read_csv(filename)
except FileNotFoundError:
    print(f"Error: Could not find {filename}. Make sure it is in the same folder.")
    exit()

# Extract columns
time_real = data['Time (s)']
speed_real = data['Speed (RPM)']
target_pwm = 60.0

# 2. Mathematical DNA (from our previous calculation)
K = 0.843
tau = 0.076

# 3. Generate the smooth Theoretical Line
# Create 100 smooth time steps from 0 to the max time of your test
time_math = np.linspace(0, time_real.max(), 100) 
# The First-Order Step Response Formula: RPM = K * PWM * (1 - e^(-t/tau))
speed_math = K * target_pwm * (1 - np.exp(-time_math / tau))

# Calculate the exact Time Constant point for the annotation
tau_speed = K * target_pwm * 0.632 # 63.2% of max speed

# 4. Draw the Graph
plt.figure(figsize=(10, 6))

# Plot the lines
plt.plot(time_real, speed_real, label='Real Sensor Data', color='red', linewidth=2)
plt.plot(time_math, speed_math, label='Theoretical Model', color='blue', linestyle='--', linewidth=2)

# Annotate the Time Constant
plt.scatter([tau], [tau_speed], color='black', zorder=5) # Put a dot exactly on the time constant
plt.annotate(f'Time Constant (\u03C4) = {tau}s\nSpeed = {round(tau_speed,1)} RPM', 
             xy=(tau, tau_speed), xytext=(tau + 0.2, tau_speed - 10),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

# Formatting to look professional
plt.title('Module 1: Motor Open-Loop Step Response (60% PWM)')
plt.xlabel('Time (seconds)')
plt.ylabel('Motor Speed (RPM)')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend()

# 5. Save the image so you can put it in your report!
plt.savefig('Module1_Graph.png', dpi=300, bbox_inches='tight')
print("✅ Saved Module1_Graph.png successfully!")