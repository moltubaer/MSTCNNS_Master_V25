
import json
import re
import csv
from collections import defaultdict

# PDU Session Establishment
#   PCF

# Set paths
path = "../data/"
input_file = "pcf_pdu_est"
output_csv = "./csv/" + input_file + ".csv"

patterns = [
    re.compile(r'"supi"\s*:\s*"imsi-\d{5,15}".*?"pduSessionId"\s*:\s*\d+', re.DOTALL),
    re.compile(r'"supi"\s*:\s*"imsi-\d{5,15}".*?"ipv4Addr"\s*:\s*"\d+\.\d+\.\d+\.\d+"', re.DOTALL)
]

# === Helper: decode hex TCP payload ===
def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        decoded_bytes = bytes.fromhex(hex_str_clean)
        decoded_text = decoded_bytes.decode("utf-8", errors="ignore")
        cleaned_text = ''.join(c for c in decoded_text if c.isprintable())
        return cleaned_text.replace('\n', '').replace('\r', '')
    except Exception:
        return ""

# === Helper: check which pattern matches ===
def match_pattern_type(decoded_text):
    for idx, pattern in enumerate(patterns):
        if pattern.search(decoded_text):
            return idx  # return 0 for first pattern, 1 for second pattern
    return None

# === Processing ===
deregistration_events = []
pattern_counters = {0: 1, 1: 1}  # Initialize counters for pattern 0 and 1

with open(path + input_file + ".json", "r") as f:
    packets = json.load(f)

# Hold per-IMSI info
session_map = defaultdict(lambda: {"recv": None, "send": None})

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_relative", "N/A")

    pkttype = layers.get("sll", {}).get("sll.pkttype")
    direction = "recv" if pkttype == "0" else "send" if pkttype == "4" else None

    if not payload or direction is None:
        continue

    decoded = decode_payload(payload)
    if not decoded.strip():
        continue

    for pattern in patterns:
        match = pattern.search(decoded)
        if match:
            # Extract IMSI (supi)
            imsi_match = re.search(r'imsi-\d{5,15}', decoded)
            if imsi_match:
                imsi = imsi_match.group(0)

                # Update only if not already set (recv) or always update for latest send
                if direction == "recv" and session_map[imsi]["recv"] is None:
                    session_map[imsi]["recv"] = {
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "direction": direction,
                        "id": imsi,
                        "decoded_payload": decoded
                    }
                elif direction == "send":
                    session_map[imsi]["send"] = {
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "direction": direction,
                        "id": imsi,
                        "decoded_payload": decoded
                    }
            break  # stop after first match

# === Write to CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "id", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for imsi, events in session_map.items():
        if events["recv"]:
            writer.writerow(events["recv"])
        if events["send"]:
            writer.writerow(events["send"])

print(f"✅ Cleaned PDU session events written to {output_csv}")