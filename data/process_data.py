import json

# Load the JSON file
with open("./captures/ue-double-reg-dereg.json", "r") as f:
    packets = json.load(f)

# NAS message type description mapping
nas_mm_message_types = {
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

# Extract and collect data
results = []
for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    frame_number = int(layers.get("frame", {}).get("frame.number", -1))
    ran_ue_ids = find_all_keys(layers, "ngap.RAN_UE_NGAP_ID")
    message_types = find_all_keys(layers, "nas_5gs.mm.message_type")
    downlink = bool(find_all_keys(layers, "ngap.DownlinkNASTransport_element"))
    uplink = bool(find_all_keys(layers, "ngap.UplinkNASTransport_element"))

    if ran_ue_ids and message_types:
        ran_ue_id = int(ran_ue_ids[0])
        for msg_type in message_types:
            # Normalize to lowercase hex string
            if isinstance(msg_type, str) and msg_type.startswith("0x"):
                msg_type_key = msg_type.lower()
            else:
                msg_type_key = hex(int(msg_type)).lower()
            description = nas_mm_message_types.get(msg_type_key, "Unknown")
            results.append({
                "frame": frame_number,
                "ran_ue_id": ran_ue_id,
                "msg_type": msg_type_key,
                "description": description,
                "downlink": downlink,
                "uplink": uplink
            })

# Sort by frame number, RAN_UE_NGAP_ID, message type
results.sort(key=lambda x: (x["frame"], x["ran_ue_id"], x["msg_type"]))

# Print results
print("\nPackets with RAN_UE_NGAP_ID, NAS 5GS message type, and direction info:\n")
for r in results:
    if r['downlink'] and r['uplink']:
        direction = "Downlink + Uplink"
    elif r['downlink']:
        direction = "Downlink"
    elif r['uplink']:
        direction = "Uplink"
    else:
        direction = "Unknown"

    print(
        f"Packet {r['frame']} \t RAN_UE_NGAP_ID: {r['ran_ue_id']} \t"
        f"Type: {r['msg_type']} \t {r['description']}   \t"
        f"Direction: {direction}"
    )
