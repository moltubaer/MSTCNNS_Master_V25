import json
import re
import csv
import string

# UE Registration
#   UDM

# Paths
path = "../data/"
input_file = "udm_ue_reg"
output_csv = "csv/" + input_file + ".csv"

# Regex
imsi_pattern = re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE)
start_pattern = re.compile(r'\{"servingNetworkName"\s*:\s*"5G:mnc\d{3}\.mcc\d{3}\.3gppnetwork\.org"\s*,\s*"ausfInstanceId"\s*:\s*"[a-f0-9\-]+"\}')

def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        decoded_bytes = bytes.fromhex(hex_str_clean)
        return ''.join(c for c in decoded_bytes.decode("utf-8", errors="ignore") if c in string.printable)
    except Exception:
        return ""

def extract_outermost_json_containing_imsi(text):
    start = text.find('{')
    if start == -1:
        return None
    stack = []
    for i in range(start, len(text)):
        if text[i] == '{':
            stack.append(i)
        elif text[i] == '}':
            stack.pop()
            if not stack:
                candidate = text[start:i+1]
                if imsi_pattern.search(candidate):
                    return candidate
    return None

# Track sessions
ue_sessions = {}
seen_ids = set()

with open(path + input_file + ".json", "r") as f:
    packets = json.load(f)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_relative", "N/A")
    pkttype = layers.get("sll", {}).get("sll.pkttype")
    direction = "recv" if pkttype == "0" else "send" if pkttype == "4" else "unknown"

    if not payload:
        continue

    decoded = decode_payload(payload)
    if not decoded.strip():
        continue

    outer_json = extract_outermost_json_containing_imsi(decoded)
    matches = imsi_pattern.findall(decoded)

    if not matches and start_pattern.search(decoded):
        if "__pending_start__" not in ue_sessions:
            ue_sessions["__pending_start__"] = {
                "start_frame": int(frame_number),
                "start_time": float(timestamp),
                "start_direction": direction,
                "start_payload": decoded,
                "end_frame": int(frame_number),
                "end_time": float(timestamp),
                "end_direction": direction,
                "end_payload": decoded
            }
        continue

    if outer_json:
        for raw_id in matches:
            norm_id = raw_id.lower()
            if norm_id in seen_ids:
                continue

            if "__pending_start__" in ue_sessions:
                ue_sessions[norm_id] = ue_sessions.pop("__pending_start__")

            if norm_id not in ue_sessions:
                ue_sessions[norm_id] = {
                    "start_frame": int(frame_number),
                    "start_time": float(timestamp),
                    "start_direction": direction,
                    "start_payload": outer_json,
                    "end_frame": int(frame_number),
                    "end_time": float(timestamp),
                    "end_direction": direction,
                    "end_payload": outer_json
                }
            else:
                ue_sessions[norm_id]["end_frame"] = int(frame_number)
                ue_sessions[norm_id]["end_time"] = float(timestamp)
                ue_sessions[norm_id]["end_direction"] = direction
                ue_sessions[norm_id]["end_payload"] = outer_json

            seen_ids.add(norm_id)

# Write CSV
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "imsi", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for imsi, session in ue_sessions.items():
        writer.writerow({
            "frame_number": session["start_frame"],
            "timestamp": f"{session['start_time']:.9f}",
            "direction": session["start_direction"],
            "imsi": imsi,
            "decoded_payload": session["start_payload"]
        })
        writer.writerow({
            "frame_number": session["end_frame"],
            "timestamp": f"{session['end_time']:.9f}",
            "direction": session["end_direction"],
            "imsi": imsi,
            "decoded_payload": session["end_payload"]
        })

print(f"✅ Registration start/end packets written to {output_csv}")
