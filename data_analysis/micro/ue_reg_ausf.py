import json
import re
import csv
import string

# UE Registration
#   AUSF, UDM

import json
import re
import csv
import string

# Paths
path = "../data/"
input_file = "ausf_ue_reg"
output_csv = "csv/" + input_file + ".csv"

# Regex
imsi_pattern = re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE)

def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        decoded_bytes = bytes.fromhex(hex_str_clean)
        return ''.join(c for c in decoded_bytes.decode("utf-8", errors="ignore") if c in string.printable)
    except Exception:
        return ""

def extract_outermost_json_containing_imsi(text):
    first_brace = text.find('{')
    if first_brace == -1:
        return None
    if first_brace + 1 < len(text) and text[first_brace + 1] == '{':
        start = first_brace + 1
    else:
        start = first_brace
    text = text[start:]

    stack = []
    for i, char in enumerate(text):
        if char == '{':
            stack.append(i)
        elif char == '}':
            if stack:
                stack.pop()
            if not stack:
                candidate = text[:i+1]
                if imsi_pattern.search(candidate):
                    return candidate
    return None

# Map SUCI to IMSI
suci_to_imsi = {}

# Collect all matches
results = []

with open(path + input_file + ".json", "r") as f:
    packets = json.load(f)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_relative", "N/A")
    pkttype = layers.get("sll", {}).get("sll.pkttype")
    direction = "recv" if pkttype == "0" else "send" if pkttype == "4" else "unknown"

    if not payload:
        continue

    decoded = decode_payload(payload)
    if not decoded.strip():
        continue

    outer_json = extract_outermost_json_containing_imsi(decoded)
    matches = imsi_pattern.findall(decoded)

    # Learn SUCI -> IMSI mapping
    for match in matches:
        if match.lower().startswith("suci") and "imsi-" in decoded.lower():
            imsi_match = re.search(r"imsi-\d{5,15}", decoded.lower())
            if imsi_match:
                suci_to_imsi[match.lower()] = imsi_match.group(0)

    # Normalize ID
    for raw_id in matches:
        candidate = raw_id.lower()
        norm_id = suci_to_imsi.get(candidate, candidate)
        results.append({
            "frame_number": int(frame_number),
            "timestamp": f"{float(timestamp):.9f}",
            "direction": direction,
            "imsi": norm_id,
            "decoded_payload": outer_json if outer_json else decoded
        })

# Write CSV
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "imsi", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"✅ Matching packets written to {output_csv}")
