import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse

# === CLI Argument ===
parser = argparse.ArgumentParser(description="Parse messages using specified NF pattern set")
parser.add_argument("--name", "-n", required=True, type=str)
parser.add_argument("--test", "-t", required=True, choices=["ue_reg", "ue_dereg", "pdu_est", "pdu_rel"], type=str)
parser.add_argument("--dir", "-d", type=str)
parser.add_argument("--output", "-o", type=str)
args = parser.parse_args()

# === Input/Output ===
# path = "../data/linear/free5gc/ue_dereg/"
path = args.dir
input_file = args.name
output_dir = args.output
output_csv = f"{output_dir}/{input_file}.csv"

# === Procedure Code Pairs (Initiating -> Release) ===
# PROCEDURE_CODE_PAIRS = [
#     {"first": "15", "release": "14"},   # UE Registration
#     {"first": "46", "release": "41"},   # UE Deregistration
#     {"first": "46", "release": "29"},   # PDU Session Establishment
#     {"first": "46", "release": "28"},   # PDU Session Release
# ]

# === Procedure Code Mapping ===
PROCEDURE_CODE_MAP = {
    "ue_reg":    {"first": "15", "release": "14"},
    "ue_dereg":  {"first": "46", "release": "41"},
    "pdu_est":   {"first": "46", "release": "29"},
    "pdu_rel":   {"first": "46", "release": "28"},
}

# === Parse PDML ===
tree = ET.parse(path + "/" + input_file + ".pdml")
root = tree.getroot()

# === Extract Relevant Packet Info ===
output = []

for packet in root.findall("packet"):
    frame_number = None
    timestamp = None
    direction = None
    current_ran_ids = []
    current_procedure_codes = []
    current_pdu_types = []

    for proto in packet.findall("proto"):
        if proto.get("name") == "frame":
            for field in proto.iter("field"):
                if field.get("name") == "frame.number":
                    frame_number = int(field.get("show"))
                elif field.get("name") == "frame.time_relative":
                    timestamp = field.get("show")

        elif proto.get("name") == "sll":
            for field in proto.iter("field"):
                if field.get("name") == "sll.pkttype":
                    val = field.get("show")
                    if val == "0":
                        direction = "recv"
                    elif val == "4":
                        direction = "send"

        elif proto.get("name") == "ngap":
            for field in proto.iter("field"):
                if field.get("name") == "ngap.RAN_UE_NGAP_ID":
                    current_ran_ids.append(field.get("show"))
                elif field.get("name") == "ngap.procedureCode":
                    current_procedure_codes.append(field.get("show"))
                elif field.get("name") == "ngap.initiatingMessage_element":
                    current_pdu_types.append("initiating")
                elif field.get("name") == "ngap.successfulOutcome_element":
                    current_pdu_types.append("successful")

    for idx, ran_id in enumerate(current_ran_ids):
        proc_code = current_procedure_codes[idx] if idx < len(current_procedure_codes) else (current_procedure_codes[-1] if current_procedure_codes else None)
        pdu_type = current_pdu_types[idx] if idx < len(current_pdu_types) else (current_pdu_types[-1] if current_pdu_types else None)

        output.append((ran_id, frame_number, timestamp, proc_code, pdu_type, direction))
        # print(f"[DEBUG] Frame {frame_number}: ran_id={ran_id}, procedureCode={proc_code}, pdu_type={pdu_type}, direction={direction}")

# === Organize by RAN UE NGAP ID ===
packets_by_id = defaultdict(list)

for ran_id, frame_number, timestamp, procedure_code, pdu_type, direction in output:
    packets_by_id[ran_id].append((frame_number, timestamp, procedure_code, pdu_type, direction))

# Select the procedure pair based on CLI input
procedure_pair = PROCEDURE_CODE_MAP[args.test]
first_code = procedure_pair["first"]
release_code = procedure_pair["release"]

# === Identify Message Pairs ===
results = []

for ran_id, packet_list in packets_by_id.items():
    first = None
    release = None

    for frame_number, timestamp, procedure_code, pdu_type, direction in sorted(packet_list):
        if procedure_code == first_code and pdu_type == "initiating" and not first:
            first = (frame_number, timestamp, direction)
        elif procedure_code == release_code and pdu_type == "initiating":
            release = (frame_number, timestamp, direction)

    if first:
        results.append({
            "id": ran_id,
            "frame_number": first[0],
            "timestamp": first[1],
            "type": "first",
            "procedure_code": first_code,
            "direction": first[2]
        })
    if release:
        results.append({
            "id": ran_id,
            "frame_number": release[0],
            "timestamp": release[1],
            "type": "release",
            "procedure_code": release_code,
            "direction": release[2]
        })

# === Write to CSV ===
print(f"[INFO] Writing results to {output_csv}")
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

with open(output_csv, "w", newline="") as csvfile:
    fieldnames = ["id", "frame_number", "timestamp", "type", "procedure_code", "direction"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print("✅ Done!")
