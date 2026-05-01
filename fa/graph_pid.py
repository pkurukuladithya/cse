import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

# Change this filename to whichever test you want to graph!
filename = "pid_test6_30rpm.csv" 

try:
    data = pd.read_csv(filename)
except FileNotFoundError:
    print(f"🚨 Error: Could not find {filename}.")
    sys.exit()

time = data['Time (s)'].values
actual = data['Actual (RPM)'].values
target_val = data['Target (RPM)'].iloc[0]

# --- 1. CALCULATE PERFORMANCE METRICS ---
# Max Overshoot (%)
max_rpm = np.max(actual)
overshoot = max(0.0, ((max_rpm - target_val) / target_val) * 100)

# Steady-State Error (%) - based on the average of the last 10% of the data
ss_rpm = np.mean(actual[-int(len(actual)*0.1):]) 
ss_error = abs((target_val - ss_rpm) / target_val) * 100

# Settling Time (Time it takes to enter and stay within +/- 2% of target)
tolerance = 0.02 * target_val
# Find all indices where the speed is OUTSIDE the 2% band
outside_band_indices = np.where(abs(actual - target_val) > tolerance)[0]
if len(outside_band_indices) > 0:
    # Settling time is the time of the LAST point outside the band
    settling_time = time[outside_band_indices[-1]]
else:
    settling_time = 0.0

# Rise Time (Time to go from 10% to 90% of target speed)
try:
    t10 = time[np.where(actual >= 0.1 * target_val)[0][0]]
    t90 = time[np.where(actual >= 0.9 * target_val)[0][0]]
    rise_time = t90 - t10
except IndexError:
    rise_time = 0.0 # If it never reached 90%

# --- 2. DRAW THE GRAPH ---
fig, ax = plt.subplots(figsize=(10, 6))

# Plot the 2% Settling Band (Gray shaded area)
ax.fill_between(time, target_val - tolerance, target_val + tolerance, 
                color='gray', alpha=0.2, label='+/- 2% Settling Band')

# The "Ultimate Smooth" 10-Point Centered Filter
# center=True ensures the smooth line doesn't lag behind the raw data
actual_smoothed = pd.Series(actual).rolling(window=10, min_periods=1, center=True).mean()

# Plot the beautiful, perfectly smooth line
ax.plot(time, actual_smoothed, 'b-', label='Smoothed Motor Speed', linewidth=2.5)

# Plot the raw, spikey data faintly in the background 
ax.plot(time, actual, 'b-', alpha=0.15, label='Raw Sensor Data')

# Plot Target Line
ax.axhline(target_val, color='r', linestyle='--', label='Target (Setpoint)')

# Formatting
ax.set_title('Module 3: PID Controller Step Response', fontweight='bold')
ax.set_xlabel('Time (Seconds)', fontweight='bold')
ax.set_ylabel('Speed (RPM)', fontweight='bold')
ax.grid(True, linestyle=':', alpha=0.7)
ax.legend(loc='upper right', fontsize='small')

# Set limits
ax.set_xlim(left=0)
ax.set_ylim(0, max(max_rpm, target_val) + 10)

# --- 3. ADD THE METRICS TEXT BOX ---
metrics_text = (
    "--- Performance Metrics ---\n"
    f"Rise Time: {rise_time:.2f} s\n"
    f"Settling Time: {settling_time:.2f} s\n"
    f"Max Overshoot: {overshoot:.1f}%\n"
    f"Steady-State Error: {ss_error:.1f}%"
)

# Place text box in the lower right corner
props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray')
ax.text(0.95, 0.05, metrics_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', horizontalalignment='right', bbox=props)

# Save the image
output_name = filename.replace('.csv', '_6.png')
plt.savefig(output_name, dpi=300, bbox_inches='tight')
print(f"✅ Saved {output_name} successfully!")