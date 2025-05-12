import subprocess
import argparse
import time
import numpy as np

import matplotlib.pyplot as plt


# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Deregister UEs via nr-cli")
parser.add_argument("--count", "-c", type=int, required=True, help="Number of UEs to deregister")
parser.add_argument("--mode", choices=["linear", "exponential"], required=True, help="Delay pattern between deregistration events")
parser.add_argument("--core", choices=["open5gs", "free5gc", "aether"], required=True, help="Type of delay buffer between UE PDU session starts")
parser.add_argument("--duration", const=0, type=int, help="Just to make it compatible with workflow script")
args = parser.parse_args()

# === CONFIGURATION ===
start_index = 1
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"
dereg_cmd = "deregister disable-5g"
mean_delay = 0.01   # 10 ms

# === Core IMSI Parameters ===
open5gs_imsi_str = "001010000000001"
free5gc_imsi_str = "208930000000001"
aether_imsi_str = "208930100006001"

# === IMSI Calculation Base ===
if args.core == "open5gs":
    base_number = int(open5gs_imsi_str)
elif args.core == "free5gc":
    base_number = int(free5gc_imsi_str)
elif args.core == "aether":
    base_number = int(aether_imsi_str)

# === Function to run one deregistration
def run_dereg(imsi):
    full_cmd = [nr_cli_path, imsi, "--exec", dereg_cmd]
    try:
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return f"✅ {imsi}: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"❌ {imsi}: {e.stderr.strip()}"

# === Delay Strategy ===
if args.mode == "exponential":
    delays = np.random.exponential(scale=mean_delay, size=args.count - 1)
else:
    delays = [mean_delay] * (args.count - 1)

# plt.hist(delays, bins=20, density=True, alpha=0.7, color='blue')
# plt.title(f"Exponential Distribution (mean = {mean_delay})")
# plt.xlabel("Delay (seconds)")
# plt.ylabel("Density")
# plt.grid(True)
# plt.show()

# === Sequential Execution with Delay ===
for i in range(start_index, start_index + args.count):
    imsi_number = base_number + (i - start_index)
    imsi = f"imsi-{imsi_number:015d}"
    print(f"🚪 Deregistering UE {imsi}")
    print(run_dereg(imsi))

    if i < start_index + args.count - 1:
        time.sleep(delays[i - start_index])
