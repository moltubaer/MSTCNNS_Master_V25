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
parser.add_argument("--pattern", required=True, type=str, help="Network Function: udm, smf, pcf")
parser.add_argument("--core", required=True, type=str, help="Core name: free5gc, open5gs, aether")
args = parser.parse_args()

# === Input/Output ===
path = args.input
input_file = args.name
output_csv = f"{args.output}/{input_file}.csv"

# === Pattern Definitions ===
pattern_pcf = [
    # re.compile(r'"supi"\s*:\s*"imsi-\d{5,15}".*?"pduSessionId"\s*:\s*\d+', re.DOTALL),
    # re.compile(r'"supi"\s*:\s*"imsi-\d{5,15}".*?"ipv4Addr"\s*:\s*"\d+\.\d+\.\d+\.\d+"', re.DOTALL),
    # re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    # re.compile(r'insert.*policyData\.ues\.chargingData.*imsi-\d{5,15}', re.IGNORECASE),

    # Open5GS
    re.compile(r'"supi"\s*:\s*"imsi-\d{5,15}"', re.IGNORECASE),
    re.compile(r'imsi\d{5,15}', re.IGNORECASE),
    # Free5GC
    re.compile(r'"supi"\s*:\s*"imsi-\d{5,15}".*"pduSessionId"\s*:\s*\d+.*"dnn"\s*:\s*".*?".*"notificationUri"\s*:\s*".*?"', re.IGNORECASE | re.DOTALL),
    re.compile(r'insert.*chargingData.*ueId\s*imsi-\d{5,15}', re.IGNORECASE | re.DOTALL)
    # Aether
]

pattern_smf = [
    # Open5GS
    re.compile(r'"supi"\s*:\s*"imsi-\d{15}".*?"pei"\s*:\s*"imeisv-\d+".*?"n1SmMsg".*?"smContextStatusUri"', re.DOTALL),
    re.compile(r'"supi"\s*:\s*"imsi-\d{15}".*?"subsSessAmbr".*?"sliceInfo"', re.DOTALL),
    # Free5GC

    # Aether
]

pattern_udm = [
    # Open5GS
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    # Free5GC
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    re.compile(r'"singleNssai"\s*:\s*{.*?"sst"\s*:\s*\d+.*?"sd"\s*:\s*"\d+".*?}\s*,\s*"dnnConfigurations"\s*:\s*{.*?"internet".*?}',re.DOTALL | re.IGNORECASE),
    # Aether
]

use_imsi_id = False

# === Select Pattern Set ===
pattern_matrix = {
    ("udm", "free5gc"): (pattern_udm, True),
    ("smf", "free5gc"): (pattern_smf, True),
    ("pcf", "free5gc"): (pattern_pcf, True),
    ("udm", "open5gs"): (pattern_udm, True),
    ("smf", "open5gs"): (pattern_smf, True),
    ("pcf", "open5gs"): (pattern_pcf, True),
    # ("udm", "aether"): (pattern_udm, True),
    # ("smf", "aether"): (pattern_smf, True),
    # ("pcf", "aether"): (pattern_pcf, True),
}

try:
    patterns, use_imsi_id = pattern_matrix[(args.pattern, args.core)]
except KeyError:
    raise ValueError(f"Unsupported combination: pattern={args.pattern}, core={args.core}")

print(patterns)

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

# def extract_ids(text):
#     match = re.search(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", text, re.IGNORECASE)
#     if not match:
#         return None

#     digits = ''.join(filter(str.isdigit, match.group(1)))
#     return int(digits[-10:]) if digits else None

def extract_ids(text):
    match = re.search(r"(?:imsi-?|suci-)(\d{5,15})", text, re.IGNORECASE)
    if not match:
        return None
    
    digits = match.group(1)
    return int(digits[-10:].lstrip("0") or "0")


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
        if use_imsi_id:
            imsi = extract_ids(decoded)
            if imsi:
                event_id = imsi
            else:
                event_id = pattern_counters[pattern_type]
                pattern_counters[pattern_type] += 1
        else:
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
