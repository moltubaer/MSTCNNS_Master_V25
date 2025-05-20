import json
import os

path = "/mnt/c/Dev/master/pcap_captures/open5gs_19.05.2025_captures/micro_data/100_linear_pdu_rel_open5gs_2025.05.19_12.58/open5gs_udm.json"
output_file = os.path.basename(path) + ".decoded.txt"

# Improved cleaner
def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        decoded_bytes = bytes.fromhex(hex_str_clean)
        decoded_text = decoded_bytes.decode("utf-8", errors="ignore")

        # Remove non-printable characters except \n \r \t
        cleaned_text = ''.join(c for c in decoded_text if c.isprintable() or c in '\n\r\t')
        return cleaned_text
    except Exception:
        return ""

# Ensure output directory exists
os.makedirs("tmp", exist_ok=True)

with open(path, "r") as f:
    packets = json.load(f)

with open("tmp/" + output_file, "w", encoding="utf-8") as out:
    for pkt in packets:
        layers = pkt.get("_source", {}).get("layers", {})
        frame_number = layers.get("frame", {}).get("frame.number", "unknown")
        tcp = layers.get("tcp", {})
        payload = tcp.get("tcp.payload")

        if not payload:
            continue

        decoded = decode_payload(payload)
        if decoded.strip():  # Only write non-empty
            line = f"Frame {frame_number}:\n{decoded}\n{'='*40}\n"
            out.write(line)

print(f"✅ Cleaned and decoded TCP payloads saved to tmp/{output_file}")
