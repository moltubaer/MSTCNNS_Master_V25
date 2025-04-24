import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# === CONFIGURATION ===
csv_file = "../capture_scripts/04.07_17:40_system.csv"
# csv_file = "/home/alexandermoltu/pcap_captures/04.09_14:04_system.csv"

# === LOAD DATA ===
df = pd.read_csv(csv_file)

# Convert Unix timestamp to float
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
df.set_index("timestamp", inplace=True)

# Optionally normalize time (seconds since start)
start_time = df["timestamp"].min()
df["time_since_start"] = df["timestamp"] - start_time

# === PLOT TOTAL CPU USAGE ===
plt.figure(figsize=(12, 4))
plt.plot(df["time_since_start"], df["cpu_total"], label="Total CPU Usage")
plt.title("Total CPU Usage Over Time")
plt.xlabel("Time Since Start (s)")
plt.ylabel("CPU Usage (%)")
plt.grid(True)
plt.tight_layout()
plt.show()

# === PLOT MEMORY USAGE ===
plt.figure(figsize=(12, 4))
plt.plot(df["time_since_start"], df["mem_used_mb"], label="Used RAM (MB)")
plt.title("RAM Usage Over Time")
plt.xlabel("Time Since Start (s)")
plt.ylabel("Memory (MB)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# === PLOT PER-CORE CPU USAGE ===
cpu_core_columns = [col for col in df.columns if col.startswith("cpu") and col != "cpu_total"]

plt.figure(figsize=(12, 6))
for col in cpu_core_columns:
    plt.plot(df["time_since_start"], df[col], label=col)

plt.title("Per-Core CPU Usage Over Time")
plt.xlabel("Time Since Start (s)")
plt.ylabel("CPU Usage (%)")
plt.legend(loc='upper right', ncol=2)
plt.grid(True)
plt.tight_layout()
plt.show()
