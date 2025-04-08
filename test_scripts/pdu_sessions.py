import subprocess
import argparse
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

import matplotlib.pyplot as plt


# === Configuration ===
mean_delay = 0.01   # 10 ms
start_index = 1
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"

# === Core IMSI Parameters ===
open5gs_imsi_str = "001010000000001"
free5gc_imsi_str = "208930000000001"
aether_imsi_str = "208930100000001"

# === Command Templates ===
pdu_establish_cmd = 'ps-establish IPv4'
pdu_release_cmd = 'ps-release-all'

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Manage PDU sessions via nr-cli")
parser.add_argument("--count", "-c", type=int, help="Number of UEs to establish sessions for (only needed when not using --kill)")
parser.add_argument("--release", action="store_true", help="Release all sessions instead of establishing them")
parser.add_argument("--mode", choices=["linear", "exponential"], required=True, help="Type of delay buffer between UE PDU session starts")
parser.add_argument("--core", choices=["open5gs", "free5gc", "aether"], required=True, help="Type of delay buffer between UE PDU session starts")
args = parser.parse_args()

# === Determine mode and count ===
mode = "release" if args.release else "establish"
count = args.count
core = args.core


if args.core == "open5gs":
    base_number = int(open5gs_imsi_str)
elif args.core == "free5gc":
    base_number = int(free5gc_imsi_str)
elif args.core == "aether":
    base_number = int(aether_imsi_str)


if count is None:
    print("❌ Please specify --count N.")
    exit(1)
elif mode is None:
    print("❌ Please specify --mode linear|exponential")
    exit(1)
elif core is None:
    print("❌ Please specify --core open5gs|fre5gc|aether")
    exit(1)


# === Function to run one command
def run_nr_cli(imsi, command):
    full_cmd = [nr_cli_path, imsi, "--exec", command]
    try:
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return f"✅ {imsi}: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"❌ {imsi}: {e.stderr.strip()}"

# === Main Execution ===
if mode == "release":
    with ThreadPoolExecutor() as executor:
        futures = []
        for i in range(start_index, start_index + count):
            imsi_number = base_number + (i - start_index)
            imsi = f"imsi-{imsi_number:015d}"
            print(f"🔻 Releasing PDU session for {imsi}")
            futures.append(executor.submit(run_nr_cli, imsi, pdu_release_cmd))
        for f in as_completed(futures):
            print(f.result())
else:
    if args.mode == "exponential":
        inter_arrival_times = np.random.exponential(scale=mean_delay, size=count - 1)
    elif args.mode == "linear":
        inter_arrival_times = [mean_delay] * (count - 1)


    # plt.hist(inter_arrival_times, bins=20, density=True, alpha=0.7, color='blue')
    # plt.title(f"Exponential Distribution (mean = {mean_delay})")
    # plt.xlabel("Delay (seconds)")
    # plt.ylabel("Density")
    # plt.grid(True)
    # plt.show()

    for i in range(start_index, start_index + count):
        imsi_number = base_number + (i - start_index)
        imsi = f"imsi-{imsi_number:015d}"
        print(f"▶️  Establishing PDU session for {imsi}")
        print(run_nr_cli(imsi, pdu_establish_cmd))

        if i < start_index + count - 1:
            delay = inter_arrival_times[i - start_index]
            time.sleep(delay)
