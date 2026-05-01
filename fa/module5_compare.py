import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np
import sys

# --- INPUT PARAMETERS ---
# Module 1 System Model (Plant)
K_plant = 0.843
Tau_plant = 0.076
# Module 5 Gains provided
Kp, Ki, Kd = 0.5, 1.6, 0.01 
TARGET = 30
DURATION = 5.0 # Seconds
SAMPLE_RATE_SIM = 0.001 # Smooth simulation resolution (1ms)

hardware_csv = "module5_hardware.csv"

print("🚀 Starting Module 5: Simulation vs Hardware Comparison...")

# --- TASK 1: MATHEMATICAL SIMULATION ---
print("📊 Step 1: Running PID Simulation math...")

# A. Plant Model (Transfer Function): G(s) = K / (Tau*s + 1)
plant_num = [K_plant]
plant_den = [Tau_plant, 1]
sys_plant = signal.TransferFunction(plant_num, plant_den)

# B. PID Controller: C(s) = (Kd*s^2 + Kp*s + Ki) / s
ctrl_num = [Kd, Kp, Ki]
ctrl_den = [1, 0] # Representing (1*s + 0)
sys_ctrl = signal.TransferFunction(ctrl_num, ctrl_den)

# C. Closed-Loop System (Feedback): T(s) = (CG) / (1 + CG)
# SciPy combines Transfer Functions serially with standard division/multiplication
numerator = np.polymul(ctrl_num, plant_num)
denominator = np.polyadd(np.polymul(ctrl_den, plant_den), np.polymul(ctrl_num, plant_num))
sys_cl = signal.TransferFunction(numerator, denominator)

# D. Run Simulation (Step Response scaled by Target RPM)
sim_time = np.arange(0, DURATION, SAMPLE_RATE_SIM)
t, y = signal.step(sys_cl, T=sim_time)
sim_actual_scaled = y * TARGET

# --- TASK 2: LOAD & SMOOTH HARDWARE DATA ---
print("📈 Step 2: Loading hardware data and applying signal filter...")
try:
    hw_data = pd.read_csv(hardware_csv)
except FileNotFoundError:
    print(f"🚨 Error: Could not find '{hardware_csv}'. Run 'module5_data_capture.py' first!")
    sys.exit()

hw_time = hw_data['Time (s)'].values
hw_actual_raw = hw_data['Actual (RPM)'].values

# Apply standard 10-point centered moving average filter for professionalism
hw_smoothed = pd.Series(hw_actual_raw).rolling(window=10, min_periods=1, center=True).mean().values

# --- TASK 3: CREATE THE COMPARISON GRAPH ---
print("🎨 Step 3: Generating final comparison plot...")
fig, ax = plt.subplots(figsize=(12, 7))

# A. Plot Target
ax.axhline(y=TARGET, color='r', linestyle='--', label='Target Setpoint (30 RPM)', linewidth=2, zorder=3)

# B. Plot Simulation (The "Ideal" mathematical truth)
ax.plot(sim_time, sim_actual_scaled, 'g-', label='Theoretical Simulation (Ideal)', linewidth=3, zorder=4)

# C. Plot Hardware (The "Physical" truth - Filtered and Raw)
ax.plot(hw_time, hw_smoothed, 'b-', label='Physical Hardware (Filtered)', linewidth=2.5, zorder=2)
# Add raw noise ghosted in background (highly recommended for Viva)
ax.plot(hw_time, hw_actual_raw, 'b-', alpha=0.15, label='Raw Hardware (Sensor Noise)', zorder=1)

# Format Graph
my_title = f"Module 5 Performance Evaluation: Simulation vs Hardware\nPlant: G(s)={K_plant}/({Tau_plant}s+1) | Controller: Kp={Kp}, Ki={Ki}, Kd={Kd}"
ax.set_title(my_title, fontsize=14, fontweight='bold')
ax.set_xlabel('Time (Seconds)', fontweight='bold')
ax.set_ylabel('Speed (RPM)', fontweight='bold')
ax.set_ylim(-2, TARGET + 10) # Dynamic ceiling
ax.set_xlim(0, DURATION)
ax.grid(True, linestyle=':', alpha=0.7)
ax.legend(loc='lower right', frameon=True, shadow=True, facecolor='white')

# Add performance metrics data box comparing Sim vs HW Settling times/Overshoot
# (Optional but recommended - requires extra math. Let's keep it clean first).

plt.tight_layout()
output_name = 'Module5_Sim_vs_Hardware.png'
plt.savefig(output_name, dpi=300, bbox_inches='tight')
print(f"✅ Success! Comparison plot generated: {output_name}")