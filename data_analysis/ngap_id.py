import argparse
import json
import csv
import os
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict

num = 500
# Argument parser for optional input file
parser = argparse.ArgumentParser(description="Parse NGAP/NAS messages by RAN_UE_NGAP_ID.")
parser.add_argument(
    "-f", "--file",
    type=str,
    # default="./captures/pdu-est-re.json",
    default="/home/alexandermoltu/master/captures/open5gs_ueransim_ue_dereg/" + str(num) + ".json",
    help="Path to the input JSON file"
)
args = parser.parse_args()

# Load the JSON file
with open(args.file, "r") as f:
    packets = json.load(f)

csv_rows = []

# NAS message type mapping
nas_descriptions = {
    "0x41": "Registration Request",
    "0x42": "Registration Accept",
    "0x43": "Registration Complete",
    "0x44": "Registration Reject",
    "0x45": "Deregistration Request (UE)",
    "0x46": "Deregistration Accept (UE)",
    "0x47": "Deregistration Request (Network)",
    "0x48": "Deregistration Accept (Network)",
    "0x55": "Identity Request",
    "0x56": "Authentication Request",
    "0x57": "Authentication Response",
    "0x58": "Authentication Reject",
    "0x59": "Authentication Failure",
    "0x5c": "Security Mode Command",
    "0x5d": "Security Mode Complete",
    "0x5e": "Security Mode Reject"
}

# NGAP procedureCode + role mapping
ngap_procedure_map = {
    (4, 0):  ("DownlinkNASTransport", "Request"),
    (4, 1):  ("DownlinkNASTransport", "Response"),
    (9, 0):  ("NGSetup", "Request"),
    (10, 0): ("UEContextReleaseRequest", "Request"),
    (11, 0): ("UplinkNASTransport", "Request"),
    (12, 0): ("DownlinkNASTransport", "Request"),
    (13, 0): ("InitialUEMessage", "Request"),
    (14, 0): ("InitialContextSetup", "Request"),
    (14, 1): ("InitialContextSetup", "Response"),
    (15, 0): ("Paging", "Request"),
    (18, 0): ("UEContextModification", "Request"),
    (19, 0): ("PathSwitchRequest", "Request"),
    (21, 0): ("InitialContextSetup (alt)", "Request"),
    (23, 0): ("PDUSessionResourceSetup", "Request"),
    (25, 0): ("PDUSessionResourceRelease", "Request"),
    (29, 0): ("PDUSessionResourceSetupRequest", "Request"),
    (29, 1): ("PDUSessionResourceSetupRelease", "Response"),
    # (29, 0): ("UEContextRelease", "Request"),
    # (29, 1): ("UEContextRelease", "Response"),
    (39, 0): ("NASNonDeliveryIndication", "Request"),
    (39, 1): ("NASNonDeliveryIndication", "Response"),
    (41, 0): ("UEContextReleaseCommand", "Request"),
    (41, 1): ("UEContextReleaseComplete", "Response"),
    (46, 0): ("UplinkNASTransport (extended)", "Request"),
    (46, 1): ("UplinkNASTransport (extended)", "Response")
}

# PDU request proc_code 29 for open5gs
# PDU request proc_code 23 for free5gc


# Recursive search for a specific key
def find_all_keys(data, target_key):
    found = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                found.append(value)
            else:
                found.extend(find_all_keys(value, target_key))
    elif isinstance(data, list):
        for item in data:
            found.extend(find_all_keys(item, target_key))
    return found

# Check if NAS is encrypted
def is_nas_encrypted(layers):
    try:
        headers = find_all_keys(layers, "nas_5gs.security_header_type")
        return any(h == "4" for h in headers)
    except:
        return False

# Group packets by ngap.RAN_UE_NGAP_ID
ue_packets = defaultdict(list)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    frame = int(layers.get("frame", {}).get("frame.number", -1))
    relative = float(layers.get("frame", {}).get("frame.time_relative", -1))
    ran_ue_ids = find_all_keys(layers, "ngap.RAN_UE_NGAP_ID")
    msg_types = find_all_keys(layers, "nas_5gs.mm.message_type")
    msg_type = msg_types[0].lower() if msg_types else None
    nas_desc = nas_descriptions.get(msg_type, "Unknown" if msg_type else "-")
    encrypted = is_nas_encrypted(layers)

    # Determine NGAP role and procedureCode
    proc_code = None
    choice_index = None
    ngap = layers.get("ngap", {})
    ngap_tree = ngap.get("ngap.NGAP_PDU_tree", {})

    if "ngap.initiatingMessage_element" in ngap_tree:
        choice_index = 0
        proc_code_raw = find_all_keys(ngap_tree["ngap.initiatingMessage_element"], "ngap.procedureCode")
    elif "ngap.successfulOutcome_element" in ngap_tree:
        choice_index = 1
        proc_code_raw = find_all_keys(ngap_tree["ngap.successfulOutcome_element"], "ngap.procedureCode")
    elif "ngap.unsuccessfulOutcome_element" in ngap_tree:
        choice_index = 2
        proc_code_raw = find_all_keys(ngap_tree["ngap.unsuccessfulOutcome_element"], "ngap.procedureCode")
    else:
        proc_code_raw = []

    try:
        proc_code = int(proc_code_raw[0]) if proc_code_raw else None
    except:
        proc_code = None

    ngap_name, ngap_role = ngap_procedure_map.get(
        (proc_code, choice_index),
        (f"Unknown (Code {proc_code})", "-")
    )

    if ran_ue_ids:
        ran_ue_id = int(ran_ue_ids[0])
        ue_packets[ran_ue_id].append({
            "frame": frame,
            "relative": relative,
            "msg_type": msg_type,
            "nas_description": nas_desc,
            "ngap_name": ngap_name,
            "ngap_role": ngap_role,
            "encrypted": encrypted
        })

# Print grouped packets and calculate timings
print("📡 Packets grouped by ngap.RAN_UE_NGAP_ID:\n")

# Define message pairs (NAS msg_type or NGAP name)
message_pairs = [
    # NAS-based
    ("0x56", "0x57", "Authentication"),
    ("0x41", "0x43", "Registration"),
    ("0x45", "0x46", "Deregistration (UE)"),
    ("0x47", "0x48", "Deregistration (NW)"),

    # NGAP-based
    ("InitialContextSetup", "InitialContextSetup", "Initial Context Setup"),
    ("PDUSessionResourceSetup", "PDUSessionResourceSetup", "PDU Session Setup"),
    ("PDUSessionResourceSetupRequest", "PDUSessionResourceSetupRelease", "PDU Session Setup"),
    ("UEContextReleaseCommand", "UEContextReleaseComplete", "Deregistration (Context Release)"),
    ("0x41", "InitialContextSetup", "Registration Phase"),
]

for ran_ue_id in sorted(ue_packets.keys()):
    print(f"--- UE {ran_ue_id} ---")
    timeline = sorted(ue_packets[ran_ue_id], key=lambda x: x["frame"])
    for pkt in timeline:
        print(f"  Frame {pkt['frame']} - t={pkt['relative']:.6f}s - "
              f"NAS: {pkt['msg_type']} - {pkt['nas_description']} | "
              f"NGAP: {pkt['ngap_name']} ({pkt['ngap_role']})"
              f"{' [Encrypted]' if pkt['encrypted'] else ''}")
    print()

    # Timing logic
    for req_type, rsp_type, label in message_pairs:
        req_pkt = None
        rsp_pkt = None

        for pkt in timeline:
            # NAS → NAS
            if req_type.startswith("0x") and rsp_type.startswith("0x"):
                if pkt["msg_type"] == req_type and not req_pkt:
                    req_pkt = pkt
                elif pkt["msg_type"] == rsp_type and req_pkt and not rsp_pkt:
                    rsp_pkt = pkt
                    break

            # NGAP → NGAP
            elif not req_type.startswith("0x") and not rsp_type.startswith("0x"):
                if pkt["ngap_name"] == req_type and pkt["ngap_role"] == "Request" and not req_pkt:
                    req_pkt = pkt
                elif pkt["ngap_name"] == rsp_type and pkt["ngap_role"] == "Response" and req_pkt and not rsp_pkt:
                    rsp_pkt = pkt
                    break

            # NAS → NGAP (special case)
            elif req_type.startswith("0x") and not rsp_type.startswith("0x"):
                if pkt["msg_type"] == req_type and not req_pkt:
                    req_pkt = pkt
                elif pkt["ngap_name"] == rsp_type and req_pkt and not rsp_pkt:
                    rsp_pkt = pkt
                    break

        if req_pkt and rsp_pkt:
            delta = rsp_pkt["relative"] - req_pkt["relative"]
            print(f"⏱️  UE {ran_ue_id}: {label} - Frame {req_pkt['frame']} → {rsp_pkt['frame']} Δt = {delta:.6f}s")
            csv_rows.append({
                "ue_id": ran_ue_id,
                "timestamp": f"{req_pkt['relative']:.6f}",
                "event_type": label,
                "latency": f"{delta:.6f}"
            })

    # Total UE lifetime
    first_pkt = timeline[0]
    last_pkt = timeline[-1]
    total_lifetime = last_pkt["relative"] - first_pkt["relative"]
    print(f"📏 UE {ran_ue_id} lifetime: Frame {first_pkt['frame']} → {last_pkt['frame']} Δt = {total_lifetime:.3f}s\n")
    print()

# Group CSV rows by event_type
grouped_csv_rows = defaultdict(list)
for row in csv_rows:
    grouped_csv_rows[row["event_type"]].append(row)

# Phase-wide summary statistics split into per-event CSV files
for event_type, rows in grouped_csv_rows.items():
    timestamps = [float(row["timestamp"]) for row in rows]
    latencies = [float(row["latency"]) for row in rows]

    if not timestamps or not latencies:
        continue

    start_time = min(timestamps)
    end_time = max([float(row["timestamp"]) + float(row["latency"]) for row in rows])
    total_duration = end_time - start_time
    average_latency = sum(latencies) / len(latencies)
    sum_all_latencies = average_latency * 100   # ONLY AN APPROXIMATION

    print(f"📊 {event_type}:")
    print(f"   Total time from first request to last response: {total_duration:.6f}s")
    print(f"   Sum of all latencies (per-UE): {sum_all_latencies:.6f}s")
    print(f"   Average UE latency: {average_latency:.6f}s")
    print(f"   Number of UEs: {num}\n")

    filename = f"tmp/{event_type.lower().replace(' ', '_')}_summary.csv"
    
    # Only write header if file is empty or doesn't exist
    write_header = not os.path.exists(filename) or os.stat(filename).st_size == 0

    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames = ["event_type", "total_duration", "average_latency", "num_ues", "sum_latencies"])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "event_type": event_type,
            "total_duration": f"{total_duration:.6f}",
            "average_latency": f"{average_latency:.6f}",
            "num_ues": num,
            "sum_latencies": f"{sum_all_latencies:.6f}"
        })

    print(f"📄 Summary appended to {filename}")
    print()