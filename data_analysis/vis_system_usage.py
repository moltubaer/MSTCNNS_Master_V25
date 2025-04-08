import pandas as pd
import matplotlib.pyplot as plt

# === CONFIGURATION ===
csv_file = "../capture_scripts/04.07_17:40_system.csv"  # Replace with your file path

# === LOAD DATA ===
df = pd.read_csv(csv_file)

# Convert timestamp to datetime for proper plotting
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%H:%M:%S.%f")
df.set_index("timestamp", inplace=True)

# === PLOT TOTAL CPU USAGE ===
plt.figure(figsize=(12, 4))
plt.plot(df.index, df["cpu_total"], label="Total CPU Usage")
plt.title("Total CPU Usage Over Time")
plt.xlabel("Time")
plt.ylabel("CPU Usage (%)")
plt.grid(True)
plt.tight_layout()
plt.show()

# === PLOT MEMORY USAGE ===
plt.figure(figsize=(12, 4))
plt.plot(df.index, df["mem_used_mb"], label="Used RAM (MB)")
plt.plot(df.index, df["mem_total_mb"], label="Total RAM (MB)", linestyle='--')
plt.title("RAM Usage Over Time")
plt.xlabel("Time")
plt.ylabel("Memory (MB)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# === PLOT PER-CORE CPU USAGE ===
cpu_core_columns = [col for col in df.columns if col.startswith("cpu") and col != "cpu_total"]

plt.figure(figsize=(12, 6))
for col in cpu_core_columns:
    plt.plot(df.index, df[col], label=col)

plt.title("Per-Core CPU Usage Over Time")
plt.xlabel("Time")
plt.ylabel("CPU Usage (%)")
plt.legend(loc='upper right', ncol=2)
plt.grid(True)
plt.tight_layout()
plt.show()
