import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

filename = "multi_step_data.csv"

# PID values for the title
Kp_val = 0.5
Ki_val = 1.6
Kd_val = 0.01

try:
    data = pd.read_csv(filename)
except FileNotFoundError:
    print(f"🚨 Error: Could not find '{filename}'. Run multi_step_test.py first.")
    sys.exit()

time = data['Time (s)'].values
actual = data['Actual (RPM)'].values
target_array = data['Target (RPM)'].values
step_ids = data['Step_ID'].values

# Smooth the actual data to filter out quantization noise for accurate math
actual_smoothed = pd.Series(actual).rolling(window=10, min_periods=1, center=True).mean().values

# --- CALCULATE METRICS PER STEP ---
metrics_text = "--- Step-by-Step Performance Analysis ---\n\n"

# Group the data by Step_ID
for step in np.unique(step_ids):
    # Extract data for just this specific step
    idx = (step_ids == step)
    step_time = time[idx]
    step_actual = actual_smoothed[idx] # Use smoothed data so spikes don't ruin the math
    target = target_array[idx][0]
    
    if target == 0:
        continue # Skip calculating metrics for the final shutdown step
        
    step_start_time = step_time[0]
    prev_target = 0 if step == 1 else target_array[step_ids == (step - 1)][0]
    is_step_up = target > prev_target

    # 1. Max Overshoot (Handles both stepping up and stepping down)
    if is_step_up:
        peak = np.max(step_actual)
        overshoot = max(0.0, ((peak - target) / target) * 100.0)
    else:
        valley = np.min(step_actual)
        overshoot = max(0.0, ((target - valley) / target) * 100.0)

    # 2. Steady-State Error (Average of the last 15% of the step duration)
    tail_idx = int(len(step_actual) * 0.85)
    steady_val = np.mean(step_actual[tail_idx:])
    sse = (abs(target - steady_val) / target) * 100.0

    # 3. Settling Time (+/- 2% Band)
    lower_bound = target * 0.98
    upper_bound = target * 1.02
    
    # Find all points where the line is OUTSIDE the 2% band
    out_of_band = np.where((step_actual < lower_bound) | (step_actual > upper_bound))[0]
    
    if len(out_of_band) == 0:
        settling_time = 0.0 # It was already inside
    elif out_of_band[-1] == len(step_actual) - 1:
        settling_time = float('inf') # It never settled!
    else:
        # The exact moment it entered the band and stayed there
        settled_idx = out_of_band[-1] + 1
        settling_time = step_time[settled_idx] - step_start_time

    # Format the text for the table
    ts_str = f"{settling_time:.2f}s" if settling_time != float('inf') else "No Settle"
    direction = "UP" if is_step_up else "DOWN"
    metrics_text += f"Step to {int(target)} RPM ({direction}):  Overshoot: {overshoot:04.1f}%  |  SSE: {sse:04.1f}%  |  Settling: {ts_str}\n"

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(12, 7)) # Taller graph to fit the new data box

# Plot Target, Smooth Actual, and Raw Actual
ax.plot(time, target_array, 'r--', label='Changing Target Setpoint', linewidth=2, zorder=3)
ax.plot(time, actual_smoothed, 'b-', label='Smoothed Motor Response', linewidth=2.5, zorder=2)
ax.plot(time, actual, 'b-', alpha=0.15, label='Raw Sensor Data', zorder=1)

# Format Graph
my_title = f"Dynamic Trajectory Tracking (Multi-Setpoint Test)\n(Kp = {Kp_val} | Ki = {Ki_val} | Kd = {Kd_val})"
ax.set_title(my_title, fontsize=14, fontweight='bold')
ax.set_xlabel('Time (Seconds)', fontweight='bold')
ax.set_ylabel('Speed (RPM)', fontweight='bold')
ax.set_ylim(-5, 55) 
ax.grid(True, linestyle=':', alpha=0.7)
ax.legend(loc='upper right')

# Add the Performance Metrics Data Box to the bottom right
props = dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', alpha=0.9, edgecolor='#ced4da')
ax.text(0.97, 0.04, metrics_text, transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', horizontalalignment='right', bbox=props, family='monospace')

plt.tight_layout()
output_filename = 'Trajectory_Tracking_Graph.png'
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"✅ Trajectory Graph generated successfully: {output_filename}")