import os
import subprocess

# To delete all JSON and PDML file recursively:
#   find /mnt/c/Dev/master/pcap_captures/aether -type f \( -name "*.json" -o -name "*.pdml" \) -delete

NF_FILTERS = {
    "aether": {
        "amf": {"filter": "kafka", "format": "json"},
        "ausf": {"filter": "tcp", "format": "json"},
        "smf": {"filter": "tcp", "format": "json"},
        "nssf": {"filter": "tcp", "format": "json"},
        "pcf": {"filter": "tcp", "format": "json"},
        "upf": {"filter": "tcp", "format": "json"},
    },
    "open5gs": {
        "amf": {"filter": "ngap", "format": "pdml"},
        "ausf": {"filter": "tcp", "format": "json"},
        "smf": {"filter": "tcp", "format": "json"},
        "nssf": {"filter": "tcp", "format": "json"},
        "pcf": {"filter": "tcp", "format": "json"},
        "upf": {"filter": "tcp", "format": "json"},
    },
    "free5gc": {
        "amf": {"filter": "ngap", "format": "pdml"},
        "ausf": {"filter": "tcp", "format": "json"},
        "smf": {"filter": "tcp", "format": "json"},
        "nssf": {"filter": "tcp", "format": "json"},
        "pcf": {"filter": "tcp", "format": "json"},
        "upf": {"filter": "tcp", "format": "json"},
    }
}

def extract_nf(file_name: str) -> str:
    name = file_name.lower()
    for nf in ["amf", "ausf", "udm", "smf", "pcf", "nrf", "bsf", "scp", "nssf", "udr", "upf"]:
        if f"_{nf}_" in name or name.startswith(f"{nf}_") or name.endswith(f"_{nf}") or f"-{nf}-" in name or f"-{nf}_" in name or f"_{nf}-" in name or name.startswith(f"{nf}-"):
            return nf
    if "ueransim" in name:
        return "ueransim"
    return "unknown"

def extract_ue_count(folder_name: str) -> str:
    parts = folder_name.split("-")
    return parts[0] if parts and parts[0].isdigit() else "X"

def convert_pcap_recursive(root_dir: str, core: str):
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if not file.endswith(".pcap"):
                continue

            input_path = os.path.join(dirpath, file)
            base_filename = os.path.splitext(file)[0]

            # Check if it's a ueransim capture
            is_ueransim = "ueransim" in file.lower()

            nf_type = None
            for nf in NF_FILTERS.get(core, {}):
                if nf in file.lower():
                    nf_type = nf
                    break

            target_subdir_name = os.path.basename(dirpath)  # Use parent folder name in all cases

            if is_ueransim:
                output_ext = ".pdml"
                tshark_format = "pdml"
                display_filter = "ngap"
                subfolder = "macro_data"

            elif nf_type:
                nf_config = NF_FILTERS[core][nf_type]
                tshark_format = nf_config["format"]
                display_filter = nf_config["filter"]
                output_ext = f".{tshark_format}"
                subfolder = "micro_data"

            else:
                output_ext = ".json"
                tshark_format = "json"
                display_filter = "tcp"
                subfolder = "micro_data"

            output_filename = f"{base_filename}{output_ext}"

            # Path 1: Save next to original pcap
            same_dir_output = os.path.join(dirpath, output_filename)

            # Path 2: Save one level up, in named subfolder
            parent_dir = os.path.dirname(dirpath)
            target_dir = os.path.join(parent_dir, subfolder, target_subdir_name)
            os.makedirs(target_dir, exist_ok=True)
            one_up_output = os.path.join(target_dir, output_filename)

            # Run tshark
            tshark_cmd = [
                "tshark",
                "-r", input_path,
                "-Y", display_filter,
                "-T", tshark_format
            ]

            try:
                result = subprocess.run(
                    tshark_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stderr = result.stderr.strip()
                output_data = result.stdout

                if stderr:
                    if "network type" in stderr or "doesn't support" in stderr:
                        print(f"[SKIP] Unsupported format: {input_path}")
                        continue
                    elif "Running as user" in stderr:
                        print(f"[OK] Converted with root warning: {input_path}")
                    else:
                        print(f"[ERROR] {input_path}: {stderr}")
                        continue
                else:
                    print(f"[OK] Converted: {input_path} -> {output_filename}")

                # Save to both locations
                with open(same_dir_output, "w") as f1, open(one_up_output, "w") as f2:
                    f1.write(output_data)
                    f2.write(output_data)

            except Exception as e:
                print(f"[FAIL] {input_path}: {e}")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recursively convert .pcap files to JSON or PDML.")
    parser.add_argument("--input", "-i", required=True, help="Root directory containing .pcap files")
    parser.add_argument("--core", "-c", required=True, choices=NF_FILTERS.keys(), help="5G core type")
    args = parser.parse_args()
    # /mnt/c/Dev/master/pcap_captures/aether

    convert_pcap_recursive(args.input, args.core)

