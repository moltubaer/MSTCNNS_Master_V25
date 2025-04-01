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

# Message pairs to track
message_pairs = {
    "0x56": "0x57",  # Auth
    "0x5c": "0x5d",  # Security
    "0x41": "0x42",  # Reg → Accept
    "0x42": "0x43",  # Accept → Complete
    "0x45": "0x46"   # Dereg
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

# Extract and enrich packet info
results = []
for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    frame_number = int(layers.get("frame", {}).get("frame.number", -1))
    timestamp = float(layers.get("frame", {}).get("frame.time_epoch", -1))
    rel_time = float(layers.get("frame", {}).get("frame.time_relative", -1))
    ran_ue_ids = find_all_keys(layers, "ngap.RAN_UE_NGAP_ID")
    message_types = find_all_keys(layers, "nas_5gs.mm.message_type")
    downlink = bool(find_all_keys(layers, "ngap.DownlinkNASTransport_element"))
    uplink = bool(find_all_keys(layers, "ngap.UplinkNASTransport_element"))

    if ran_ue_ids and message_types:
        ran_ue_id = int(ran_ue_ids[0])
        for msg_type in message_types:
            if isinstance(msg_type, str) and msg_type.startswith("0x"):
                msg_type_key = msg_type.lower()
            else:
                msg_type_key = hex(int(msg_type)).lower()
            description = nas_mm_message_types.get(msg_type_key, "Unknown")
            results.append({
                "frame": frame_number,
                "timestamp": timestamp,
                "relative": rel_time,
                "ran_ue_id": ran_ue_id,
                "msg_type": msg_type_key,
                "description": description,
                "downlink": downlink,
                "uplink": uplink
            })

# Sort by time
results.sort(key=lambda x: x["timestamp"])

# Analyze timing between related messages
print("\n⏱️ Timing Analysis Between NAS Message Pairs:\n")
pending = {}

for entry in results:
    ue_id = entry["ran_ue_id"]
    msg_type = entry["msg_type"]
    key = (ue_id, msg_type)

    if msg_type in message_pairs:
        pending[key] = entry
    elif any(msg_type == resp for resp in message_pairs.values()):
        for req_type, resp_type in message_pairs.items():
            if resp_type == msg_type:
                req_key = (ue_id, req_type)
                if req_key in pending:
                    req = pending[req_key]
                    delta = entry["timestamp"] - req["timestamp"]
                    print(
                        f"UE {ue_id}: {req['description']} (Frame {req['frame']}, t={req['relative']:.6f}s) "
                        f"→ {entry['description']} (Frame {entry['frame']}, t={entry['relative']:.6f}s) "
                        f"Δ = {delta:.3f} s"
                    )
                    del pending[req_key]
                break
