import time
import psutil
from datetime import datetime
import os
import argparse

# ToDo: Change to linux time
# Problem: this script starts after the tcpdump finishes

# === Argument Parsing ===
parser = argparse.ArgumentParser(description="Capture system metrics to CSV")
parser.add_argument("--duration", "-d", type=int, default=120, help="Capture duration in seconds")
args = parser.parse_args()

duration = args.duration
interval = 0.2
outdir = "/home/ubuntu/pcap_captures"
# outdir = "."
os.makedirs(outdir, exist_ok=True)
outfile = os.path.join(outdir, datetime.now().strftime("%Y.%m.%d_%H.%M")+"_system.csv")
num_cores = psutil.cpu_count()

# Warm up: let psutil collect initial CPU stats
psutil.cpu_percent(interval=None, percpu=True)
time.sleep(interval)

# Header
with open(outfile, "w") as f:
    headers = ["timestamp", "cpu_total"] + [f"cpu{i}" for i in range(num_cores)] + ["mem_used_mb", "mem_percent"]
    f.write(",".join(headers) + "\n")

# Logging loop
start = time.time()
while time.time() - start < duration:
    timestamp = f"{time.time():.3f}"  # Unix time in seconds.milliseconds
    cpu_all = psutil.cpu_percent(interval=None, percpu=True)
    mem = psutil.virtual_memory()

    avg_cpu = sum(cpu_all) / len(cpu_all)
    row = [timestamp, f"{avg_cpu:.2f}"] + [f"{c:.2f}" for c in cpu_all]
    row += [f"{mem.used // (1024 * 1024)}", f"{mem.percent:.2f}"]

    with open(outfile, "a") as f:
        f.write(",".join(row) + "\n")

    time.sleep(interval)

# Change ownership after capture is done
os.system(f"chown ubuntu:ubuntu {outfile}")