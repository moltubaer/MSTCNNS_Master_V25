import subprocess
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Manage PDU sessions via nr-cli")
parser.add_argument("--count", type=int, help="Number of UEs to establish sessions for (only needed when not using --kill)")
parser.add_argument("--kill", action="store_true", help="Release all sessions instead of establishing them")
args = parser.parse_args()

# === CONFIGURATION ===
start_index = 1
base_imsi_str = "208930000000001"
default_release_count = 1000
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"
max_concurrent = 100  # Limit concurrent PDU requests

# === Command Templates ===
pdu_establish_cmd = 'ps-establish IPv4 --sst 1 -n internet'
pdu_release_cmd = 'ps-release-all'
base_number = int(base_imsi_str)

# === Determine mode and count ===
mode = "kill" if args.kill else "establish"
count = default_release_count if args.kill else args.count

if count is None:
    print("❌ Please specify --count N when establishing PDU sessions.")
    exit(1)

# === Function to run one command
def run_nr_cli(imsi, command):
    full_cmd = [nr_cli_path, imsi, "--exec", command]
    try:
        time.sleep(0.001)  # 1 ms buffer
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        return f"✅ {imsi}: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"❌ {imsi}: {e.stderr.strip()}"

# === Threaded Execution with max 100 workers
with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
    futures = []
    for i in range(start_index, start_index + count):
        imsi_number = base_number + (i - start_index)
        imsi = f"imsi-{imsi_number:015d}"
        command = pdu_release_cmd if args.kill else pdu_establish_cmd
        print(f"{'🔻 Releasing' if args.kill else '▶️  Establishing'} PDU session for {imsi}")
        futures.append(executor.submit(run_nr_cli, imsi, command))

    for f in as_completed(futures):
        print(f.result())
