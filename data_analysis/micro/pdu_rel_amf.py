import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

# PDU Session Release
#   AMF

# === Paths ===
path = "/home/alexandermoltu/pcap_captures/full_test_core/pdu_rel/100-open5gs-2025.04.28_12.29.59/"
input_file = "amf"
output_csv = "./csv/" + input_file + "_pdu_rel.csv"

# === Helpers ===
def get_field(proto, name):
    for field in proto.iter("field"):
        if field.get("name") == name:
            return field.get("show")
    return None

# === Parse PDML ===
tree = ET.parse(path + input_file + ".pdml")
root = tree.getroot()

packets = []

for packet in root.findall('packet'):
    frame_number = None
    timestamp = None
    ran_ids = []
    procedure_code = None
    direction = None
    pdu_type = None  # initiatingMessage, successfulOutcome, etc.

    for proto in packet.findall('proto'):
        proto_name = proto.get('name')

        if proto_name == 'frame':
            frame_number = int(get_field(proto, 'frame.number'))
            timestamp = get_field(proto, 'frame.time_epoch')

        if proto_name == 'sll':
            pkttype = get_field(proto, 'sll.pkttype')
            if pkttype == '0':
                direction = 'recv'
            elif pkttype == '4':
                direction = 'send'

        if proto_name == 'ngap':
            for field in proto.iter('field'):
                if field.get('name') == 'ngap.RAN_UE_NGAP_ID':
                    ran_ids.append(field.get('show'))
                if field.get('name') == 'ngap.procedureCode':
                    procedure_code = field.get('show')
                if field.get('name') in ('ngap.initiatingMessage_element', 'ngap.successfulOutcome_element', 'ngap.unsuccessfulOutcome_element'):
                    pdu_type = field.get('name').split('.')[1].replace('_element', '')

    for ran_id in ran_ids:
        packets.append((ran_id, frame_number, timestamp, procedure_code, direction, pdu_type))

# === Process into output structure ===
seen = {}
results = []

for ran_id, frame_number, timestamp, procedure_code, direction, pdu_type in packets:
    if ran_id not in seen:
        seen[ran_id] = {}

    if 'first' not in seen[ran_id]:
        seen[ran_id]['first'] = (frame_number, timestamp, direction)
    elif procedure_code == '28' and pdu_type == 'initiatingMessage' and direction == 'send':
        seen[ran_id]['release'] = (frame_number, timestamp, direction)

# === Write results ===
os.makedirs("./csv", exist_ok=True)
with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ran_ue_ngap_id", "frame_number", "timestamp", "type", "direction"])
    for ran_id, data in seen.items():
        if 'first' in data:
            writer.writerow([ran_id, data['first'][0], data['first'][1], "first", data['first'][2]])
        if 'release' in data:
            writer.writerow([ran_id, data['release'][0], data['release'][1], "release", data['release'][2]])

print("[INFO] Writing results to", output_csv)
print("✅ Done!")
