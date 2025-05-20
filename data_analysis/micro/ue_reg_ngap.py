import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse

# UE Registration
#   AMF

# === CLI Argument ===
parser = argparse.ArgumentParser(description="Parse messages using specified NF pattern set")
parser.add_argument("--name", "-n", required=True, type=str)
parser.add_argument("--input", "-i", type=str, help="Input directory")
parser.add_argument("--output", "-o", default=".csv", type=str)
parser.add_argument("--pattern", "-p", type=str)
parser.add_argument("--core", "-c", type=str)
args = parser.parse_args()

# === Input/Output ===
# path = "../data/linear/open5gs/ue_reg/"
path = args.input
input_file = args.name  # 100.amf.ue_reg.pdml
output_csv = f"{args.output}/{input_file}.csv"


# === Constants ===
FIRST_PROCEDURE_CODE = "15"  # InitialUEMEssage
RELEASE_PROCEDURE_CODE = "14"  # InitialContextSetup

# === Parse PDML ===
tree = ET.parse(os.path.join(path, input_file))
root = tree.getroot()

# === Extract Relevant Packet Info ===
output = []

for packet in root.findall("packet"):
    frame_number = None
    timestamp = None
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

    # Match RAN UE IDs with their proc_code and pdu_type
    for idx, ran_id in enumerate(current_ran_ids):
        proc_code = current_procedure_codes[idx] if idx < len(current_procedure_codes) else (current_procedure_codes[-1] if current_procedure_codes else None)
        pdu_type = current_pdu_types[idx] if idx < len(current_pdu_types) else (current_pdu_types[-1] if current_pdu_types else None)

        output.append((ran_id, frame_number, timestamp, proc_code, pdu_type))
        # print(f"[DEBUG] Frame {frame_number}: ran_id={ran_id}, procedureCode={proc_code}, pdu_type={pdu_type}")

# === Organize by RAN UE NGAP ID ===
packets_by_id = defaultdict(list)

for ran_id, frame_number, timestamp, procedure_code, pdu_type in output:
    packets_by_id[ran_id].append((frame_number, timestamp, procedure_code, pdu_type))

# === Identify First and Release Messages ===
results = []

for ran_id, packet_list in packets_by_id.items():
    first = None
    release = None

    for frame_number, timestamp, procedure_code, pdu_type in sorted(packet_list):
        if procedure_code == FIRST_PROCEDURE_CODE and pdu_type == "initiating" and not first:
            first = (frame_number, timestamp)
        elif procedure_code == RELEASE_PROCEDURE_CODE and pdu_type == "initiating":
            release = (frame_number, timestamp)

    if first:
        results.append({
            "id": ran_id,
            "frame_number": first[0],
            "timestamp": first[1],
            "type": "first",
            "direction": "recv"
        })
    if release:
        results.append({
            "id": ran_id,
            "frame_number": release[0],
            "timestamp": release[1],
            "type": "release",
            "direction": "send"
        })

# === Write to CSV ===
print(f"[INFO] Writing results to {output_csv}")
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

with open(output_csv, "w", newline="") as csvfile:
    fieldnames = ["id", "frame_number", "timestamp", "type", "direction"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print("✅ Done!")
