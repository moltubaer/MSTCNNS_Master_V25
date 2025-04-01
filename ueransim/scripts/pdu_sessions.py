import subprocess
import argparse

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Manage PDU sessions via nr-cli")
parser.add_argument("--count", type=int, default=1000, help="Number of UEs to manage")
parser.add_argument("--kill", action="store_true", help="Release sessions instead of establishing them")
args = parser.parse_args()

# === CONFIGURATION ===
start_index = 1
base_imsi_str = "001010000000001"
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"

# === Command Templates ===
pdu_establish_cmd = 'ps-establish IPv4 --sst 1 -n internet'
pdu_release_cmd = 'ps-release-all'

# === IMSI Calculation Base ===
base_number = int(base_imsi_str)

# === Main Loop ===
for i in range(start_index, start_index + args.count):
    imsi_number = base_number + (i - start_index)
    imsi = f"imsi-{imsi_number:015d}"
    command = pdu_release_cmd if args.kill else pdu_establish_cmd
    full_cmd = [nr_cli_path, imsi, "--exec", command]

    try:
        print(f"{'🔻 Releasing' if args.kill else '▶️  Establishing'} PDU session for {imsi}")
        result = subprocess.Popen(full_cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed for {imsi}: {e.stderr}")
