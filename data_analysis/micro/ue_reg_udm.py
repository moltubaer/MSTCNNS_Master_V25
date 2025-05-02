import json
import re
import csv

# UE Deregistration
#   UDM

# === Set input/output paths ===
path = "../data/core_ue_reg_100/"
input_file = "udm_ue_reg"
output_csv = "csv/" + input_file + ".csv"

# === Deregistration regex patterns ===
patterns = [
    # Start: servingNetworkName and ausfInstanceId
    re.compile(
        r'"servingNetworkName"\s*:\s*"5G:mnc\d{3}\.mcc\d{3}\.3gppnetwork\.org"\s*,\s*"ausfInstanceId"\s*:\s*"[a-f0-9-]+"',
        re.IGNORECASE
    ),
    # End: authenticationVector with xresStar and supi
    re.compile(
        r'"authType"\s*:\s*"5G_AKA"\s*,\s*"authenticationVector"\s*:\s*\{[^}]*?"xresStar"\s*:\s*"[a-f0-9]+"\s*,[^}]*?\}\s*,\s*"supi"\s*:\s*"imsi-\d+"',
        re.DOTALL | re.IGNORECASE
    )
]

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

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_relative", "N/A")
    srcport = int(layers.get("tcp", {}).get("tcp.srcport", 0))
    dstport = int(layers.get("tcp", {}).get("tcp.dstport", 0))

    sll = layers.get("sll", {})
    pkttype = sll.get("sll.pkttype")
    if pkttype == "0":
        direction = "recv"
    elif pkttype == "4":
        direction = "send"

    # direction = "send" if srcport > dstport else "recv"

    if not payload:
        continue

    decoded = decode_payload(payload)

    pattern_type = match_pattern_type(decoded)

    if decoded.strip() and pattern_type is not None:
        event_id = pattern_counters[pattern_type]
        pattern_counters[pattern_type] += 1

        deregistration_events.append({
            "frame_number": frame_number,
            "timestamp": timestamp,
            "direction": direction,
            "id": event_id,
            "decoded_payload": decoded
        })

# === Write to CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "id", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(deregistration_events)

print(f"✅ Deregistration events with IDs saved to {output_csv}")
