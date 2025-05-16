import json
import re
import csv
import os
import argparse

# UE Registration
#   AUSF, PCF, UDM

# === CLI Argument ===
parser = argparse.ArgumentParser(description="Parse messages using specified NF pattern set")
parser.add_argument("--name", "-n", required=True, type=str)
parser.add_argument("--input", "-i", type=str, help="Input directory")
parser.add_argument("--output", "-o", default=".csv", type=str)
parser.add_argument("--pattern", type=str)
args = parser.parse_args()

# === Input/Output ===
# path = "../data/linear/open5gs/ue_reg/"
path = args.input
input_file = args.name  # 100.udm.ue_reg.json
output_csv = f"{args.output}/{input_file}.csv"


# === Pattern Definitions ===
pattern_udm = [
    re.compile(
        r'"servingNetworkName"\s*:\s*"5G:mnc\d{3}\.mcc\d{3}\.3gppnetwork\.org"\s*,\s*"ausfInstanceId"\s*:\s*"[a-f0-9-]+"',
        re.IGNORECASE
    ),
    re.compile(
        r'"authType"\s*:\s*"5G_AKA"\s*,\s*"authenticationVector"\s*:\s*\{[^}]*?"xresStar"\s*:\s*"[a-f0-9]+"\s*,[^}]*?\}\s*,\s*"supi"\s*:\s*"imsi-\d+"',
        re.DOTALL | re.IGNORECASE
    ),
]
pattern_ausf = [
    # re.compile(r'"avType"\s*:\s*"5G_HE_AKA"', re.IGNORECASE),
    # re.compile(r'"kausf"\s*:\s*"[a-f0-9]{64}"', re.IGNORECASE),
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
]
pattern_pcf = [
    # re.compile(r'"policyAssociationId"\s*:\s*"[a-zA-Z0-9_-]+"', re.IGNORECASE),
    # re.compile(r'"trigger"\s*:\s*"REGISTRATION"', re.IGNORECASE),
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
]

# === Select Pattern Set ===
if args.pattern == "udm":
    patterns = pattern_udm
elif args.pattern == "ausf":
    patterns = pattern_ausf
elif args.pattern == "pcf":
    patterns = pattern_pcf
else:
    raise ValueError(f"Unknown pattern set: {args.pattern}")

# === Decode TCP Payload ===
def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        decoded_bytes = bytes.fromhex(hex_str_clean)
        decoded_text = decoded_bytes.decode("utf-8", errors="ignore")
        return ''.join(c for c in decoded_text if c.isprintable()).replace('\n', '').replace('\r', '')
    except Exception:
        return ""

# === Match Pattern Type ===
def match_pattern_type(decoded_text):
    for idx, pattern in enumerate(patterns):
        if pattern.search(decoded_text):
            return idx
    return None

# === Process PCAP JSON ===
events = []
pattern_counters = {0: 1, 1: 1}

with open(os.path.join(path, input_file), "r") as f:
    packets = json.load(f)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_relative", "N/A")

    sll = layers.get("sll", {})
    pkttype = sll.get("sll.pkttype")
    if pkttype == "0":
        direction = "recv"
    elif pkttype == "4":
        direction = "send"
    else:
        direction = "unknown"

    if not payload:
        continue

    decoded = decode_payload(payload)
    pattern_type = match_pattern_type(decoded)

    if decoded.strip() and pattern_type is not None:
        event_id = pattern_counters[pattern_type]
        pattern_counters[pattern_type] += 1

        events.append({
            "frame_number": frame_number,
            "timestamp": timestamp,
            "direction": direction,
            "id": event_id,
            "decoded_payload": decoded
        })

# === Save CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "id", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(events)

print(f"✅ Parsed {len(events)} events to {output_csv} using pattern: {args.pattern}")
