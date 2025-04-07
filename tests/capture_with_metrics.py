import time
import psutil
from datetime import datetime

# Todo:
#   1. change timestamps to seconds only
#   2. dynamic outputfile nameing

interval = 0.5       # seconds
duration = 60        # total runtime
outfile = "resource_log.csv"
num_cores = psutil.cpu_count()

# Warm up: let psutil collect initial CPU stats
psutil.cpu_percent(interval=None, percpu=True)
time.sleep(interval)

# Header
with open(outfile, "w") as f:
    headers = ["timestamp", "cpu_total"] + [f"cpu{i}" for i in range(num_cores)] + ["mem_used_mb", "mem_total_mb", "mem_percent"]
    f.write(",".join(headers) + "\n")

# Logging loop
start = time.time()
while time.time() - start < duration:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    cpu_all = psutil.cpu_percent(interval=None, percpu=True)
    mem = psutil.virtual_memory()

    avg_cpu = sum(cpu_all) / len(cpu_all)
    row = [timestamp, f"{avg_cpu:.2f}"] + [f"{c:.2f}" for c in cpu_all]
    row += [f"{mem.used // (1024 * 1024)}", f"{mem.total // (1024 * 1024)}", f"{mem.percent:.2f}"]

    with open(outfile, "a") as f:
        f.write(",".join(row) + "\n")

    time.sleep(interval)
