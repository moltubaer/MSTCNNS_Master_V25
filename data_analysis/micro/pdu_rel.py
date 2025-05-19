import json
import re
import os
import csv
import argparse
from collections import defaultdict

# PDU Session Release

# === CLI Argument ===
parser = argparse.ArgumentParser(description="Parse messages using specified NF pattern set")
parser.add_argument("--pattern", "-p", type=str, required=True, help="Name of pattern to use (e.g. udm, ausf, pcf)")
parser.add_argument("--name", "-n", required=True, type=str)
parser.add_argument("--input", "-i", type=str, help="Input directory")
parser.add_argument("--output", "-o", default=".csv", type=str)
args = parser.parse_args()

# === Input/Output ===
# path = "../data/linear/open5gs/pdu_rel"
path = args.input
input_file = args.name  # 100.smf.pdu_rel.json
output_csv = f"{args.output}/{input_file}.csv"


# === Pattern Definitions ===
pattern_smf = [
    # Open5GS
    # re.compile(r'\{"n1SmMsg":\{"contentId":"5gnas-sm"\}\}'),
    # re.compile(r'\{"n1SmMsg":\{"contentId":"5gnas-sm"\},"n2SmInfo":\{"contentId":"ngap-sm"\},"n2SmInfoType":"PDU_RES_REL_CMD"\}'),
    # Free5GC
    re.compile(r'"n1SmMsg"\s*:\s*{\s*"contentId"\s*:\s*"PDUSessionReleaseCommand"}\s*,\s*"n2SmInfo"\s*:\s*{\s*"contentId"\s*:\s*"PDUResourceReleaseCommand"}\s*,\s*"n2SmInfoType"\s*:\s*"PDU_RES_REL_CMD"', re.IGNORECASE),
    re.compile(r'grant_type=client_credentials&[^ ]*nfType=SMF[^ ]*scope=npcf-smpolicycontrol', re.IGNORECASE),
    # Aether

]

pattern_pcf = [
    # Open5GS

    # Free5GC
    re.compile(r"grant_type=client_credentials.*?nfType=PCF.*?scope=nudr-dr", re.IGNORECASE),
    re.compile(r'\{.*?"access_token"\s*:\s*".+?".*?"scope"\s*:\s*"nudr-dr".*?\}', re.IGNORECASE),
    # Aether

]

pattern_udm = [
    # Open5GS

    # Free5GC
    re.compile(r"grant_type=client_credentials.*?nfType=UDM.*?scope=nudr-dr", re.IGNORECASE),
    re.compile(r'\{.*?"access_token"\s*:\s*".+?".*?"scope"\s*:\s*"nudr-dr".*?\}', re.IGNORECASE),
    # Aether

]

# === Select Pattern Set ===
if args.pattern == "smf":
    patterns = pattern_smf
elif args.pattern == "pcf":
    patterns = pattern_pcf
elif args.pattern == "udm":
    patterns = pattern_udm
else:
    raise ValueError(f"Unknown pattern set: {args.pattern}")

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
pattern_counters = defaultdict(lambda: 1)

with open(os.path.join(path, input_file), "r") as f:
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
    else:
        direction = "unknown"

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
            "decoded_payload": decoded    # Don't print because of linebreaks in the csv file.
        })

# === Write to CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "id", "decoded_payload"]    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(deregistration_events)

print(f"✅ Deregistration events with IDs saved to {output_csv}")
