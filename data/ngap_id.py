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

# NGAP procedureCode mapping
ngap_procedure_map = {
    "4":  "DownlinkNASTransport",
    "9":  "NGSetup",
    "10": "UEContextRelease",
    "11": "UplinkNASTransport",
    "12": "DownlinkNASTransport",
    "13": "InitialUEMessage",
    "14": "InitialContextSetup",
    "15": "Paging",
    "18": "UEContextModification",
    "19": "PathSwitchRequest",
    "21": "InitialContextSetup (alt)",
    "23": "PDUSessionResourceSetup",
    "25": "PDUSessionResourceRelease",
    "41": "NASNonDeliveryIndication",
    "46": "UplinkNASTransport (extended)"
}

# Recursive key search
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

# Detect NGAP message role and extract procedure code safely
def get_ngap_role_and_proc_code(layers):
    try:
        ngap_tree = layers["ngap"].get("ngap.NGAP_PDU_tree", {})
        if "ngap.initiatingMessage_element" in ngap_tree:
            return "Request", ngap_tree["ngap.initiatingMessage_element"].get("ngap.procedureCode")
        elif "ngap.successfulOutcome_element" in ngap_tree:
            return "Response", ngap_tree["ngap.successfulOutcome_element"].get("ngap.procedureCode")
        elif "ngap.unsuccessfulOutcome_element" in ngap_tree:
            return "Reject", ngap_tree["ngap.unsuccessfulOutcome_element"].get("ngap.procedureCode")
        else:
            return "-", None
    except:
        return "-", None

# Detect if NAS is encrypted
def is_nas_encrypted(layers):
    try:
        header_types = find_all_keys(layers, "nas_5gs.security_header_type")
        return any(ht == "4" for ht in header_types)
    except:
        return False

# Group packets by RAN_UE_NGAP_ID
ue_packets = defaultdict(list)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    frame = int(layers.get("frame", {}).get("frame.number", -1))
    relative = float(layers.get("frame", {}).get("frame.time_relative", -1))
    ran_ue_ids = find_all_keys(layers, "ngap.RAN_UE_NGAP_ID")
    msg_types = find_all_keys(layers, "nas_5gs.mm.message_type")
    msg_type = msg_types[0].lower() if msg_types else None
    nas_desc = nas_descriptions.get(msg_type, "Unknown" if msg_type else "-")

    ngap_role, proc_code = get_ngap_role_and_proc_code(layers)
    ngap_name = ngap_procedure_map.get(proc_code, f"Unknown (Code {proc_code})" if proc_code else "-")
    encrypted = is_nas_encrypted(layers)

    if ran_ue_ids:
        ran_ue_id = int(ran_ue_ids[0])
        ue_packets[ran_ue_id].append({
            "frame": frame,
            "relative": relative,
            "msg_type": msg_type,
            "nas_description": nas_desc,
            "ngap_code": proc_code,
            "ngap_name": ngap_name,
            "ngap_role": ngap_role,
            "encrypted": encrypted
        })

# Sort and print per RAN_UE_NGAP_ID
print("📡 Packets grouped by ngap.RAN_UE_NGAP_ID:\n")
for ran_ue_id in sorted(ue_packets.keys()):
    print(f"--- UE {ran_ue_id} ---")
    for pkt in sorted(ue_packets[ran_ue_id], key=lambda x: x["frame"]):
        print(f"  Frame {pkt['frame']} - t={pkt['relative']:.6f}s - "
              f"NAS: {pkt['msg_type']} - {pkt['nas_description']} | "
              f"NGAP: {pkt['ngap_name']} ({pkt['ngap_role']})"
              f"{' [Encrypted]' if pkt['encrypted'] else ''}")
    print()
