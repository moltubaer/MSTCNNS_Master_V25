import argparse
import json
import csv
import os
from collections import defaultdict
from typing import List, Dict, Any, Tuple

# Constants
NUM_UES = 500
DEFAULT_JSON_PATH = f"/home/ubuntu/pcap_captures/{NUM_UES}.json"
TMP_DIR = "tmp"

# NAS message type mapping
NAS_DESCRIPTIONS = {
    "0x41": "Registration Request",
    "0x43": "Registration Complete",
    "0x56": "Authentication Request",
    "0x57": "Authentication Response",
    # Add more mappings as needed
}

# NGAP procedureCode + role mapping
NGAP_PROCEDURE_MAP = {
    (14, 0): ("InitialContextSetup", "Request"),
    (14, 1): ("InitialContextSetup", "Response"),
    (41, 0): ("UEContextReleaseCommand", "Request"),
    (41, 1): ("UEContextReleaseComplete", "Response"),
    # Add more mappings as needed
}

MESSAGE_PAIRS = [
    ("0x41", "0x43", "Registration"),
    ("0x56", "0x57", "Authentication"),
    ("InitialContextSetup", "InitialContextSetup", "Initial Context Setup"),
    ("UEContextReleaseCommand", "UEContextReleaseComplete", "Deregistration"),
]

# Helper Functions
def find_all_keys(data: Any, target_key: str) -> List[Any]:
    """Recursively find all occurrences of a key in a nested structure."""
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

def is_nas_encrypted(layers: Dict[str, Any]) -> bool:
    """Check if NAS messages are encrypted."""
    headers = find_all_keys(layers, "nas_5gs.security_header_type")
    return any(h == "4" for h in headers)

def process_packets(packets: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Group packets by ngap.RAN_UE_NGAP_ID."""
    ue_packets = defaultdict(list)
    for pkt in packets:
        layers = pkt.get("_source", {}).get("layers", {})
        frame = int(layers.get("frame", {}).get("frame.number", -1))
        relative = float(layers.get("frame", {}).get("frame.time_relative", -1))
        ran_ue_ids = find_all_keys(layers, "ngap.RAN_UE_NGAP_ID")
        msg_types = find_all_keys(layers, "nas_5gs.mm.message_type")
        msg_type = msg_types[0].lower() if msg_types else None
        nas_desc = NAS_DESCRIPTIONS.get(msg_type, "Unknown" if msg_type else "-")
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
        except ValueError:
            proc_code = None

        ngap_name, ngap_role = NGAP_PROCEDURE_MAP.get(
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
    return ue_packets

def calculate_latencies(ue_packets: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Calculate latencies for defined message pairs."""
    csv_rows = []
    for ran_ue_id, timeline in ue_packets.items():
        timeline = sorted(timeline, key=lambda x: x["frame"])
        for req_type, rsp_type, label in MESSAGE_PAIRS:
            req_pkt = None
            rsp_pkt = None
            for pkt in timeline:
                if req_type.startswith("0x") and rsp_type.startswith("0x"):
                    if pkt["msg_type"] == req_type and not req_pkt:
                        req_pkt = pkt
                    elif pkt["msg_type"] == rsp_type and req_pkt and not rsp_pkt:
                        rsp_pkt = pkt
                        break
                elif not req_type.startswith("0x") and not rsp_type.startswith("0x"):
                    if pkt["ngap_name"] == req_type and pkt["ngap_role"] == "Request" and not req_pkt:
                        req_pkt = pkt
                    elif pkt["ngap_name"] == rsp_type and pkt["ngap_role"] == "Response" and req_pkt and not rsp_pkt:
                        rsp_pkt = pkt
                        break
            if req_pkt and rsp_pkt:
                delta = rsp_pkt["relative"] - req_pkt["relative"]
                csv_rows.append({
                    "ue_id": ran_ue_id,
                    "timestamp": f"{req_pkt['relative']:.6f}",
                    "event_type": label,
                    "latency": f"{delta:.6f}"
                })
    return csv_rows

def write_csv_summary(event_type: str, rows: List[Dict[str, Any]]):
    """Write summary statistics to a CSV file."""
    filename = f"{TMP_DIR}/{event_type.lower().replace(' ', '_')}_summary.csv"
    os.makedirs(TMP_DIR, exist_ok=True)
    write_header = not os.path.exists(filename) or os.stat(filename).st_size == 0
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event_type", "total_duration", "average_latency", "num_ues", "effective_num_ues", "sum_latencies"])
        if write_header:
            writer.writeheader()
        writer.writerows(rows)

# Main Script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse NGAP/NAS messages by RAN_UE_NGAP_ID.")
    parser.add_argument("-f", "--file", type=str, default=DEFAULT_JSON_PATH, help="Path to the input JSON file")
    args = parser.parse_args()

    with open(args.file, "r") as f:
        packets = json.load(f)

    ue_packets = process_packets(packets)
    csv_rows = calculate_latencies(ue_packets)

    # Group rows by event type and write summaries
    grouped_csv_rows = defaultdict(list)
    for row in csv_rows:
        grouped_csv_rows[row["event_type"]].append(row)

    for event_type, rows in grouped_csv_rows.items():
        write_csv_summary(event_type, rows)