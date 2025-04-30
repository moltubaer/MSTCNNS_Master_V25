import xml.etree.ElementTree as ET
import csv
import os
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
NGAP_PROCEDURE_CODE = "ngap.procedureCode"
NAS_MESSAGE_TYPE = "nas_5gs.mm.message_type"
RAN_UE_NGAP_ID = "ngap.RAN_UE_NGAP_ID"
SECURITY_HEADER_TYPE = "nas_5gs.security_header_type"

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
    (13, 0): ("InitialUEMessage", "Request"),
    (14, 0): ("InitialContextSetup", "Request"),
    (14, 1): ("InitialContextSetup", "Response"),
    (41, 0): ("UEContextReleaseCommand", "Request"),
    (41, 1): ("UEContextReleaseComplete", "Response"),
}

# Recursive search for a specific field in PDML
def find_all_fields(element, target_name):
    """Recursively find all occurrences of a field in a PDML element."""
    for field in element.findall(".//field"):
        if field.get("name") == target_name:
            yield field.get("value")

# Check if NAS is encrypted
def is_nas_encrypted(packet):
    """Check if NAS messages are encrypted."""
    for value in find_all_fields(packet, SECURITY_HEADER_TYPE):
        if value == "4":
            return True
    return False

# Extract NGAP procedure codes
def extract_ngap_procedure_codes(packet):
    """Extract NGAP procedure codes from a PDML packet."""
    proc_codes = list(find_all_fields(packet, NGAP_PROCEDURE_CODE))
    return [int(code) for code in proc_codes if code.isdigit()]

# Process PDML packets
def process_pdml(file_path):
    """Process a PDML file and group packets by RAN_UE_NGAP_ID."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Group packets by RAN_UE_NGAP_ID
    ue_packets = group_packets_by_ran_ue_id(root)

    return ue_packets

def group_packets_by_ran_ue_id(root):
    """Group packets by RAN_UE_NGAP_ID."""
    ue_packets = defaultdict(list)

    for packet in root.findall(".//packet"):
        frame = -1
        relative = -1.0

        # Extract frame and timestamp
        for proto in packet.findall('proto'):
            proto_name = proto.get('name')

            if proto_name == 'frame':
                for field in proto.iter('field'):
                    if field.get('name') == 'frame.number':
                        frame = int(field.get('show'))
                    if field.get('name') == 'frame.time_epoch':
                        relative = float(field.get('show'))

        if frame == -1 or relative == -1.0:
            logging.warning(f"Skipping packet with missing frame or timestamp: {packet}")
            continue

        # Extract NGAP-related fields
        for proto in packet.findall('proto'):
            proto_name = proto.get('name')

            if proto_name == 'ngap':
                ran_ue_ids = list(find_all_fields(packet, RAN_UE_NGAP_ID))
                proc_codes = extract_ngap_procedure_codes(packet)

                for idx, proc_code in enumerate(proc_codes):
                    ngap_name, ngap_role = ngap_procedure_map.get(
                        (proc_code, 0),  # Assuming choice_index = 0 for simplicity
                        (f"Unknown (Code {proc_code})", "-")
                    )

                    if ran_ue_ids:
                        ran_ue_id = int(ran_ue_ids[idx]) if idx < len(ran_ue_ids) else int(ran_ue_ids[0])
                        ue_packets[ran_ue_id].append({
                            "frame": frame,
                            "relative": relative,
                            "msg_type": None,  # Update if needed
                            "nas_description": None,  # Update if needed
                            "ngap_name": ngap_name,
                            "ngap_role": ngap_role,
                            "encrypted": False  # Update if needed
                        })

    return ue_packets


def write_grouped_packets_to_csv(ue_packets, output_csv):
    """Write grouped packets to a CSV file in the desired format."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    with open(output_csv, "w", newline="") as csvfile:
        fieldnames = ["ran_ue_ngap_id", "frame_number", "timestamp", "type", "direction"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for ran_ue_ngap_id, packets in ue_packets.items():
            # Sort packets by frame number or timestamp if needed
            packets = sorted(packets, key=lambda pkt: pkt["frame"])

            for idx, packet in enumerate(packets):
                # Determine type
                if idx == 0:
                    packet_type = "first"
                elif packet["ngap_name"] == "UEContextReleaseCommand":
                    packet_type = "release"
                else:
                    packet_type = "other"

                # Determine direction
                direction = "recv" if packet["ngap_role"] == "Request" else "send"

                # Write to CSV
                writer.writerow({
                    "ran_ue_ngap_id": ran_ue_ngap_id,
                    "frame_number": packet["frame"],
                    "timestamp": packet["relative"],
                    "type": packet_type,
                    "direction": direction
                })


# Main script
if __name__ == "__main__":
    marcus_path = "/Users/marcusjohannessen/Desktop/NTNU/vår-2025/"
    pkt_file = "pkt_50"
    pdml_file = marcus_path + pkt_file + ".pdml"  # Replace with your PDML file path
    output_csv = "./csv/" + pkt_file + "_grouped.csv"

    # Process the PDML file
    ue_packets = process_pdml(pdml_file)

    # Write grouped packets to CSV
    write_grouped_packets_to_csv(ue_packets, output_csv)

    print(f"✅ Grouped packets written to {output_csv}")