import subprocess

# === CONFIGURATION ===
start_index = 1
end_index = 5
base_imsi_str = "001010000000001"  # base IMSI (15-digit numeric)
nr_cli_path = "/home/ubuntu/UERANSIM/build/nr-cli"  # Path to your compiled nr-cli

# === PDU Session Command Parameters ===
pdu_command = 'ps-establish IPv4 --sst 1 -n internet'

# === IMSI Calculation ===
base_number = int(base_imsi_str)

# === Loop through IMSIs and trigger session ===
for i in range(start_index, end_index + 1):
    imsi_number = base_number + (i - start_index)
    imsi = f"imsi-{imsi_number:015d}"
    full_cmd = ["sudo", nr_cli_path, imsi, "--exec", pdu_command]

    try:
        print(f"▶️  Triggering PDU session for {imsi}")
        result = subprocess.run(full_cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed for {imsi}: {e.stderr}")
