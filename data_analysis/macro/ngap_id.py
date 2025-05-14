import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import csv
import argparse

parser = argparse.ArgumentParser(description="Parse messages using specified NF pattern set")
parser.add_argument("--input", "-i", type=str, help="Input directory")
parser.add_argument("--output", "-o", type=str, help="Input directory")
args = parser.parse_args()

# Define root paths
# input_root = "/mnt/c/Dev/master/pcap_captures/test/pdml"
# output_root = "/mnt/c/Dev/master/pcap_captures/test/csv"
input_root = args.input
output_root = args.output

# Map filename keywords to test types
FILENAME_TEST_MAP = {
    "run_ues": "ue_reg",
    "ue_dereg": "ue_dereg",
    "pdu_sessions": "pdu_est",
    "pdu_release": "pdu_rel",
    "ue_reg": "ue_reg",
    "ue_dereg": "ue_dereg",
    "pdu_est": "pdu_est",
    "pdu_rel": "pdu_rel"
}

# NGAP procedure mapping
PROCEDURE_CODE_MAP = {
    "ue_reg":    {"first": "15", "release": "14"},
    "ue_dereg":  {"first": "46", "release": "41"},
    "pdu_est":   {"first": "46", "release": "29"},
    "pdu_rel":   {"first": "46", "release": "28"},
}

def determine_test_type(filename: str) -> str:
    for keyword, test in FILENAME_TEST_MAP.items():
        if keyword in filename:
            return test
    raise ValueError(f"Cannot determine test type from filename: {filename}")


def process_pdml_file(input_path: str, test_type: str, output_csv: str):
    tree = ET.parse(input_path)
    root = tree.getroot()
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
                        direction = "recv" if val == "0" else "send" if val == "4" else None
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
            proc_code = current_procedure_codes[idx] if idx < len(current_procedure_codes) else current_procedure_codes[-1]
            pdu_type = current_pdu_types[idx] if idx < len(current_pdu_types) else current_pdu_types[-1]
            output.append((ran_id, frame_number, timestamp, proc_code, pdu_type, direction))

    packets_by_id = defaultdict(list)
    for ran_id, frame_number, timestamp, procedure_code, pdu_type, direction in output:
        packets_by_id[ran_id].append((frame_number, timestamp, procedure_code, pdu_type, direction))

    procedure_pair = PROCEDURE_CODE_MAP[test_type]
    first_code = procedure_pair["first"]
    release_code = procedure_pair["release"]
    results = []

    for ran_id, packet_list in packets_by_id.items():
        first = None
        release = None
        for frame_number, timestamp, procedure_code, pdu_type, direction in sorted(packet_list):
            if procedure_code == first_code and pdu_type == "initiating" and not first:
                first = (frame_number, timestamp, direction)
            elif procedure_code == release_code and pdu_type in ("initiating", "successful"):
                release = (frame_number, timestamp, direction)
        if first:
            results.append({"id": ran_id, "frame_number": first[0], "timestamp": first[1], "type": "first", "procedure_code": first_code, "direction": first[2]})
        if release:
            results.append({"id": ran_id, "frame_number": release[0], "timestamp": release[1], "type": "release", "procedure_code": release_code, "direction": release[2]})

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "frame_number", "timestamp", "type", "procedure_code", "direction"])
        writer.writeheader()
        writer.writerows(results)


# === WALK FILES ===
for dirpath, _, filenames in os.walk(input_root):
    for file in filenames:
        if file.endswith(".pdml"):
            pdml_path = os.path.join(dirpath, file)
            rel_path = os.path.relpath(dirpath, input_root)
            output_dir = os.path.join(output_root, rel_path)
            output_csv = os.path.join(output_dir, os.path.splitext(file)[0] + ".csv")
            try:
                test_type = determine_test_type(file.lower())
                print(f"[INFO] Processing: {pdml_path} as {test_type}")
                process_pdml_file(pdml_path, test_type, output_csv)
            except ValueError as ve:
                print(f"[SKIP] {file}: {ve}")

print("✅ All done!")
