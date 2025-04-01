import subprocess
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Deregister UEs via nr-cli")
parser.add_argument("--count", type=int, required=True, help="Number of UEs to deregister")
args = parser.parse_args()

# === CONFIGURATION ===
start_index = 1
base_imsi_str = "001010000000001"
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"
max_concurrent = 100  # Limit concurrent dereg requests
dereg_cmd = "deregister disable-5g"

# === IMSI Calculation Base ===
base_number = int(base_imsi_str)

# === Function to run one deregistration
def run_dereg(imsi):
    full_cmd = [nr_cli_path, imsi, "--exec", dereg_cmd]
    try:
        time.sleep(0.001)  # 1 ms buffer
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return f"✅ {imsi}: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"❌ {imsi}: {e.stderr.strip()}"

# === Threaded Execution with max 100 workers
with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
    futures = []
    for i in range(start_index, start_index + args.count):
        imsi_number = base_number + (i - start_index)
        imsi = f"imsi-{imsi_number:015d}"
        print(f"🚪 Deregistering UE {imsi}")
        futures.append(executor.submit(run_dereg, imsi))

    for f in as_completed(futures):
        print(f.result())

# === Clean up any lingering UE processes ===
try:
    print("🧹 Killing lingering nr-ue processes...")
    subprocess.run(["sudo", "pkill", "-f", "nr-ue"], check=True)
    print("✅ All nr-ue processes terminated.")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to terminate nr-ue processes: {e}")
