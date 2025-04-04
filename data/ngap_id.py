import json
from collections import defaultdict

# Load the JSON file
with open("./captures/ue-double-reg-dereg.json", "r") as f:
    packets = json.load(f)

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
    (29, 0): ("UEContextRelease", "Request"),
    (29, 1): ("UEContextRelease", "Response"),
    (39, 0): ("NASNonDeliveryIndication", "Request"),
    (39, 1): ("NASNonDeliveryIndication", "Response"),
    (41, 0): ("UEContextReleaseCommand", "Request"),
    (41, 1): ("UEContextReleaseComplete", "Response"),
    (46, 0): ("UplinkNASTransport (extended)", "Request"),
    (46, 1): ("UplinkNASTransport (extended)", "Response")
}

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

# Print grouped packets
print("📡 Packets grouped by ngap.RAN_UE_NGAP_ID:\n")
for ran_ue_id in sorted(ue_packets.keys()):
    print(f"--- UE {ran_ue_id} ---")
    for pkt in sorted(ue_packets[ran_ue_id], key=lambda x: x["frame"]):
        print(f"  Frame {pkt['frame']} - t={pkt['relative']:.6f}s - "
              f"NAS: {pkt['msg_type']} - {pkt['nas_description']} | "
              f"NGAP: {pkt['ngap_name']} ({pkt['ngap_role']})"
              f"{' [Encrypted]' if pkt['encrypted'] else ''}")
    print()
