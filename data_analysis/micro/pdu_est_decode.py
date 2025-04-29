import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

# === Paths ===
path = "/home/alexandermoltu/pcap_captures/full_test_core/pdu_est/100-open5gs-2025.04.28_12.27.02/"
input_file = "amf"
output_csv = "./csv/" + input_file + "_pdu_est.csv"

# === Constants ===
FIRST_PROCEDURE_CODE = "46"  # Uplink NAS Transport
RELEASE_PROCEDURE_CODE = "29"  # PDU Session Resource Setup Request

# Open and parse the PDML
tree = ET.parse(path + input_file + ".pdml")
root = tree.getroot()

output = []

# Step 1: Parse packets
for packet in root.findall('packet'):
    frame_number = None
    timestamp = None
    current_ran_ids = []
    current_procedure_codes = []
    current_pdu_types = []  # NEW: to capture whether it's request or response

    for proto in packet.findall('proto'):
        proto_name = proto.get('name')

        if proto_name == 'frame':
            for field in proto.iter('field'):
                if field.get('name') == 'frame.number':
                    frame_number = int(field.get('show'))
                if field.get('name') == 'frame.time_epoch':
                    timestamp = field.get('show')

        if proto_name == 'ngap':
            for field in proto.iter('field'):
                if field.get('name') == 'ngap.RAN_UE_NGAP_ID':
                    ran_id = field.get('show')
                    current_ran_ids.append(ran_id)
                if field.get('name') == 'ngap.procedureCode':
                    proc_code = field.get('show')
                    current_procedure_codes.append(proc_code)
                if field.get('name') == 'ngap.initiatingMessage_element':
                    current_pdu_types.append('initiating')
                if field.get('name') == 'ngap.successfulOutcome_element':
                    current_pdu_types.append('successful')

    # Match each RAN UE NGAP ID to its procedureCode and pdu_type carefully
    for idx, ran_id in enumerate(current_ran_ids):
        proc_code = current_procedure_codes[idx] if idx < len(current_procedure_codes) else (current_procedure_codes[-1] if current_procedure_codes else None)
        pdu_type = current_pdu_types[idx] if idx < len(current_pdu_types) else (current_pdu_types[-1] if current_pdu_types else None)

        output.append((ran_id, frame_number, timestamp, proc_code, pdu_type))
        print(f"[DEBUG] Frame {frame_number}, RAN_UE_NGAP_ID={ran_id}, ProcedureCode={proc_code}, PDUType={pdu_type}")

# Step 2: Organize by ran_ue_ngap_id
packets_by_id = defaultdict(list)

for ran_id, frame_number, timestamp, procedure_code, pdu_type in output:
    packets_by_id[ran_id].append((frame_number, timestamp, procedure_code, pdu_type))

results = []

for ran_id, packet_list in packets_by_id.items():
    first = None
    release = None

    for frame_number, timestamp, procedure_code, pdu_type in sorted(packet_list):
        if procedure_code == FIRST_PROCEDURE_CODE and not first:
            first = (frame_number, timestamp)
        elif procedure_code == RELEASE_PROCEDURE_CODE and pdu_type == "initiating":
            release = (frame_number, timestamp)

    if first:
        results.append({
            "ran_ue_ngap_id": ran_id,
            "frame_number": first[0],
            "timestamp": first[1],
            "type": "first",
            "direction": "recv",
        })
    if release:
        results.append({
            "ran_ue_ngap_id": ran_id,
            "frame_number": release[0],
            "timestamp": release[1],
            "type": "release",
            "direction": "send",
        })

# Step 3: Write to CSV
print("[INFO] Writing results to", output_csv)
os.makedirs(os.path.dirname(output_csv), exist_ok=True)

with open(output_csv, "w", newline="") as csvfile:
    fieldnames = ["ran_ue_ngap_id", "frame_number", "timestamp", "type", "direction"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print("✅ Done!")
