import json
import re
import os
import csv
import argparse

# UE Deregistration
#   UDM

# === CLI Argument ===
parser = argparse.ArgumentParser(description="Parse messages using specified NF pattern set")
parser.add_argument("--name", "-n", required=True, type=str)
parser.add_argument("--input", "-i", type=str, help="Input directory")
parser.add_argument("--output", "-o", default=".csv", type=str)
parser.add_argument("--pattern", required=True, type=str, help="Network Function: udm, smf")
parser.add_argument("--core", required=True, type=str, help="Core name: free5gc, open5gs, aether")
args = parser.parse_args()

# === Input/Output ===
# path = "../data/linear/open5gs/ue_dereg"
path = args.input
input_file = args.name  # 100.udm.ue_dereg.json
output_csv = f"{args.output}/{input_file}.csv"

# === Deregistration regex patterns ===
pattern_udm = [
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    # Open5GS
    re.compile(r'\{"guami"\s*:\s*\{"plmnId"\s*:\s*\{"mcc"\s*:\s*"\d{3}",\s*"mnc"\s*:\s*"\d{2,3}"\},\s*"amfId"\s*:\s*"\d+"\},\s*"purgeFlag"\s*:\s*true\}',re.IGNORECASE),
    re.compile(r'\[\s*\{"op"\s*:\s*"replace",\s*"path"\s*:\s*"?PurgeFlag"?,\s*"value"\s*:\s*true\}\s*\]',re.IGNORECASE),
    # re.compile(r'"purgeFlag"\s*:\s*true', re.IGNORECASE),
    # re.compile(r'\{"op":"replace","path":"PurgeFlag","value":true\}'),
    # Free5GC
    re.compile(r'grant_type=client_credentials.*?nfType=UDM.*?scope=nudr-dr.*?targetNfType=UDR', re.IGNORECASE),
    re.compile(r'\{"guami"\s*:\s*\{"plmnId"\s*:\s*\{"mcc"\s*:\s*"\d{3}",\s*"mnc"\s*:\s*"\d{2,3}"\},\s*"amfId"\s*:\s*"[a-zA-Z0-9]+"\},\s*"purgeFlag"\s*:\s*true\}', re.IGNORECASE),
    # Aether


    # Open5GS
    # No identifiable messages
    # Free5GC
    re.compile(r"grant_type=client_credentials.*?nfType=UDM.*?scope=nudr-dr", re.IGNORECASE),
    re.compile(r'\{.*?"access_token"\s*:\s*".+?".*?"scope"\s*:\s*"nudr-dr".*?\}', re.IGNORECASE),
    # Aether

]

pattern_smf = [
    re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE),
    # Open5GS
    # No identifiable messages
    # Free5GC
    re.compile(r'"purgeFlag"\s*:\s*true', re.IGNORECASE),
    re.compile(r'\{"op":"replace","path":"PurgeFlag","value":true\}'),
    # Aether

    # Open5GS
    re.compile(r'\{"n1SmMsg":\{"contentId":"5gnas-sm"\}\}'),
    re.compile(r'\{"n1SmMsg":\{"contentId":"5gnas-sm"\},"n2SmInfo":\{"contentId":"ngap-sm"\},"n2SmInfoType":"PDU_RES_REL_CMD"\}'),
    # Free5GC
    re.compile(r'"n1SmMsg"\s*:\s*{\s*"contentId"\s*:\s*"PDUSessionReleaseCommand"}\s*,\s*"n2SmInfo"\s*:\s*{\s*"contentId"\s*:\s*"PDUResourceReleaseCommand"}\s*,\s*"n2SmInfoType"\s*:\s*"PDU_RES_REL_CMD"', re.IGNORECASE),
    re.compile(r'grant_type=client_credentials&[^ ]*nfType=SMF[^ ]*scope=npcf-smpolicycontrol', re.IGNORECASE),
    # Aether

]

pattern_pcf = [
    # Open5GS
    re.compile(r".?b\*ԎZKRX\+\$MTd0\S*"),
    re.compile(r'"servingNetwork"\s*:\s*\{"mcc"\s*:\s*"\d{3}",\s*"mnc"\s*:\s*"\d{2,3}"\}\s*,\s*"ranNasRelCauses"\s*:\s*\[\s*\{"ngApCause"\s*:\s*\{"group"\s*:\s*\d+,\s*"value"\s*:\s*\d+\},\s*"5gMmCause"\s*:\s*\d+,\s*"5gSmCause"\s*:\s*\d+\}'),
    # Free5GC
    re.compile(r"grant_type=client_credentials.*?nfType=PCF.*?scope=nudr-dr", re.IGNORECASE),
    re.compile(r'\{.*?"access_token"\s*:\s*".+?".*?"scope"\s*:\s*"nudr-dr".*?\}', re.IGNORECASE),
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

# print(patterns)

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
# pattern_counters = {0: 1, 1: 1}
pattern_counters = {i: 1 for i in range(len(patterns))}

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
