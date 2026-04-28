import pandas as pd
import matplotlib.pyplot as plt

# File names for your 3 tests
files = {
    "40% Duty Cycle": "open_loop_40pct.csv",
    "60% Duty Cycle": "open_loop_60pct.csv",
    "80% Duty Cycle": "open_loop_80pct.csv"
}

colors = {"40% Duty Cycle": "red", "60% Duty Cycle": "orange", "80% Duty Cycle": "blue"}

plt.figure(figsize=(10, 6))

# Loop through each file and plot it
for label, filename in files.items():
    try:
        data = pd.read_csv(filename)
        plt.plot(data['Time (s)'], data['Speed (RPM)'], label=label, color=colors[label], linewidth=1.5)
    except FileNotFoundError:
        print(f"⚠️ Warning: Could not find {filename}. Skipping...")

# Formatting to match the academic style
plt.title('Module 1: Motor Open-Loop Step Responses', fontweight='bold', fontsize=12)
plt.xlabel('Time (Seconds)', fontweight='bold')
plt.ylabel('Speed (RPM)', fontweight='bold')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend(loc='lower right')

# Limit axes to start at 0
plt.xlim(left=0)
plt.ylim(bottom=0)

plt.savefig('Module1_Combined_Graph.png', dpi=300, bbox_inches='tight')
print("✅ Saved Module1_Combined_Graph.png successfully!")