import pandas as pd
import matplotlib.pyplot as plt
import sys

# Change this to the CSV you generated during your Pinch Test!
filename = "final_pid_30rpm.csv"

try:
    data = pd.read_csv(filename)
except FileNotFoundError:
    print(f"🚨 Error: Could not find {filename}.")
    sys.exit()

time = data['Time (s)'].values
actual = data['Actual (RPM)'].values
target_val = data['Target (RPM)'].iloc[0]

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(10, 6))

# 1. Plot the Target Line
ax.axhline(y=target_val, color='r', linestyle='--', label='Target (Setpoint)', linewidth=2)

# 2. Plot the Smoothed Actual Data (10-point centered filter)
actual_smoothed = pd.Series(actual).rolling(window=10, min_periods=1, center=True).mean()
ax.plot(time, actual_smoothed, 'b-', label='Smoothed Motor Speed', linewidth=2.5)

# 3. Plot the Raw Data in the background
ax.plot(time, actual, 'b-', alpha=0.15, label='Raw Sensor Data')

# --- ADDING PROFESSIONAL ANNOTATIONS ---
# You may need to adjust the 'xy' coordinates depending on exactly when you pinched it!
ax.annotate('Load Applied\n(Speed Drops)', 
            xy=(5.0, 20), xycoords='data', # The point of the arrow (Time: 5s, RPM: 20)
            xytext=(3.0, 10), textcoords='data', # The text location
            arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8),
            fontsize=11, fontweight='bold', color='red')

ax.annotate('Load Removed\n(Controller Recovers)', 
            xy=(8.0, 30), xycoords='data', 
            xytext=(9.0, 15), textcoords='data',
            arrowprops=dict(facecolor='green', shrink=0.05, width=2, headwidth=8),
            fontsize=11, fontweight='bold', color='green')

# --- FORMATTING ---
ax.set_title('Module 4: Disturbance Rejection & Robustness Test\n(Kp = 0.5 | Ki = 1.6 | Kd = 0.01)', fontsize=14, fontweight='bold')
ax.set_xlabel('Time (Seconds)', fontweight='bold')
ax.set_ylabel('Speed (RPM)', fontweight='bold')
ax.set_ylim(0, 50) 
ax.grid(True, linestyle=':', alpha=0.7)
ax.legend(loc='upper right')

plt.tight_layout()
plt.savefig('Disturbance_Test_Graph.png', dpi=300, bbox_inches='tight')
print("✅ Disturbance Graph generated: Disturbance_Test_Graph.png")