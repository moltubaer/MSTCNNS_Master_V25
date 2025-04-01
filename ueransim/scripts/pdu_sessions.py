import subprocess
import argparse
import time

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Manage PDU sessions via nr-cli")
parser.add_argument("--count", type=int, help="Number of UEs to establish sessions for (only needed when not using --kill)")
parser.add_argument("--kill", action="store_true", help="Release all sessions instead of establishing them")
args = parser.parse_args()

# === CONFIGURATION ===
start_index = 1
base_imsi_str = "001010000000001"
default_release_count = 1000  # How many IMSIs to iterate when --kill is used
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"

# === Command Templates ===
pdu_establish_cmd = 'ps-establish IPv4 --sst 1 -n internet'
pdu_release_cmd = 'ps-release-all'

# === IMSI Calculation Base ===
base_number = int(base_imsi_str)

# === Determine mode and count ===
mode = "kill" if args.kill else "establish"
count = default_release_count if args.kill else args.count

if count is None:
    print("❌ Please specify --count N when establishing PDU sessions.")
    exit(1)

# === Process Execution ===
processes = []
imsi_list = []

for i in range(start_index, start_index + count):
    imsi_number = base_number + (i - start_index)
    imsi = f"imsi-{imsi_number:015d}"
    command = pdu_release_cmd if args.kill else pdu_establish_cmd
    full_cmd = [nr_cli_path, imsi, "--exec", command]

    print(f"{'🔻 Releasing' if args.kill else '▶️  Establishing'} PDU session for {imsi}")
    proc = subprocess.Popen(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    processes.append(proc)
    imsi_list.append(imsi)

    time.sleep(0.001)  # 1 ms buffer between launches

# === Collect Output ===
for imsi, proc in zip(imsi_list, processes):
    stdout, stderr = proc.communicate()
    if proc.returncode == 0:
        print(f"✅ {imsi}: {stdout.strip()}")
    else:
        print(f"❌ {imsi}: {stderr.strip()}")
