
import json
import re
import csv

# PDU Session Establishment
#   PCF, SMF, UDM

# Set paths
path = "/home/alexandermoltu/pcap_captures/full_test_core/pdu_est/100-open5gs-2025.04.28_12.27.02/"
input_file = "smf"
output_csv = "./csv/" + input_file + "_pdu_rel.csv"

# Regex to match IMSI and SUCI
imsi_pattern = re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE)

def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        return bytes.fromhex(hex_str_clean).decode("utf-8", errors="ignore")
    except Exception:
        return ""

def extract_outermost_json_containing_imsi(text):
    first_brace = text.find('{')
    if first_brace == -1:
        return None
    if first_brace + 1 < len(text) and text[first_brace + 1] == '{':
        start = first_brace + 1
    else:
        start = first_brace
    text = text[start:]

    stack = []
    for i, char in enumerate(text):
        if char == '{':
            stack.append(i)
        elif char == '}':
            if stack:
                stack.pop()
            if not stack:
                candidate = text[:i+1]
                if imsi_pattern.search(candidate):
                    return candidate
    return None

def normalize_identity(imsi_or_suci):
    if imsi_or_suci.startswith("suci-"):
        return imsi_or_suci
    return imsi_or_suci

# Track UE sessions
ue_sessions = {}

with open(path + input_file + ".json", "r") as f:
    packets = json.load(f)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_epoch", "N/A")
    direction = "unknown"

    sll = layers.get("sll", {})
    pkttype = sll.get("sll.pkttype")
    if pkttype == "0":
        direction = "recv"
    elif pkttype == "4":
        direction = "send"

    if not payload:
        continue

    decoded = decode_payload(payload)

    if decoded.strip():
        matches = imsi_pattern.findall(decoded)
        if matches:
            outer_json = extract_outermost_json_containing_imsi(decoded)
            if outer_json:
                for raw_id in matches:
                    norm_id = normalize_identity(raw_id)

                    if '"supi":"' in outer_json:
                        match = re.search(r'"supi":"(imsi-\d+)"', outer_json)
                        if match:
                            norm_id = match.group(1)

                    if norm_id not in ue_sessions:
                        ue_sessions[norm_id] = {
                            "start_frame": int(frame_number),
                            "start_time": float(timestamp),
                            "start_payload": outer_json,
                            "start_dir": direction,
                            "end_frame": int(frame_number),
                            "end_time": float(timestamp),
                            "end_payload": outer_json,
                            "end_dir": direction
                        }
                    else:
                        ue_sessions[norm_id]["end_frame"] = int(frame_number)
                        ue_sessions[norm_id]["end_time"] = float(timestamp)
                        ue_sessions[norm_id]["end_payload"] = outer_json
                        ue_sessions[norm_id]["end_dir"] = direction

# Write to CSV
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "imsi", "event", "direction", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for imsi, session in ue_sessions.items():
        writer.writerow({
            "frame_number": session["start_frame"],
            "timestamp": f"{session['start_time']:.9f}",
            "imsi": imsi,
            "event": "start",
            "direction": session["start_dir"],
            "decoded_payload": session["start_payload"]
        })
        writer.writerow({
            "frame_number": session["end_frame"],
            "timestamp": f"{session['end_time']:.9f}",
            "imsi": imsi,
            "event": "end",
            "direction": session["end_dir"],
            "decoded_payload": session["end_payload"]
        })

print(f"✅ Registration start/end packets with direction written to {output_csv}")
