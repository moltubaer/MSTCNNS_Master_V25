import os
import subprocess

# To delete all JSON and PDML file recursively:
#   find /mnt/c/Dev/master/pcap_captures -type f \( -name "*.json" -o -name "*.pdml" \) -delete


def extract_nf(file_name: str) -> str:
    for nf in ["amf", "ausf", "udm", "smf", "pcf", "nrf", "bsf", "scp", "nssf", "udr", "upf"]:
        if f"_{nf}_" in file_name.lower():
            return nf
    return "unknown"

def extract_ue_count(folder_name: str) -> str:
    parts = folder_name.split("-")
    return parts[0] if parts and parts[0].isdigit() else "X"

def convert_pcap_recursive(root_dir: str):
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if not file.endswith(".pcap"):
                continue

            input_path = os.path.join(dirpath, file)

            # Choose output format and filter
            nf = extract_nf(file)
            if nf == "amf":
                output_ext = ".pdml"
                tshark_format = "pdml"
                display_filter = "ngap"
            else:
                output_ext = ".json"
                tshark_format = "json"
                display_filter = "tcp"

            # Build output filename dynamically
            parent_dir = os.path.basename(dirpath)
            grandparent_dir = os.path.basename(os.path.dirname(dirpath))
            ue_count = extract_ue_count(parent_dir)
            output_filename = f"{nf}.{grandparent_dir}{ue_count}{output_ext}"
            output_path = os.path.join(dirpath, output_filename)

            tshark_cmd = [
                "tshark",
                "-r", input_path,
                "-Y", display_filter,
                "-T", tshark_format
            ]

            try:
                with open(output_path, "w") as out_file:
                    result = subprocess.run(
                        tshark_cmd,
                        stdout=out_file,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    stderr = result.stderr.strip()
                    if stderr:
                        if "network type" in stderr or "doesn't support" in stderr:
                            print(f"[SKIP] Unsupported format: {input_path}")
                            os.remove(output_path) if os.path.exists(output_path) else None
                        elif "Running as user" in stderr:
                            print(f"[OK] Converted with root warning: {input_path} -> {output_filename}")
                        else:
                            print(f"[ERROR] {input_path}: {stderr}")
                    else:
                        print(f"[OK] Converted: {input_path} -> {output_filename}")

            except Exception as e:
                print(f"[FAIL] {input_path}: {e}")

if __name__ == "__main__":
    root = "/mnt/c/Dev/master/pcap_captures"  # Set your root dir
    convert_pcap_recursive(root)
