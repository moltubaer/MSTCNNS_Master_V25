import json
import re
import csv

# amf, ausf and udm

# Set paths
path = "/home/alexandermoltu/pcap_captures/full_test_core/ue_reg/100-open5gs-2025.04.28_11.59.09/"
input_file = "udm.json"
output_csv = input_file + "_ue_reg.csv"

# Regex pattern to match full IMSI and SUCI
imsi_pattern = re.compile(r"(imsi-\d{5,15}|suci-\d+(?:-\d+){5,})", re.IGNORECASE)

def decode_payload(hex_str):
    try:
        hex_str_clean = hex_str.replace(":", "")
        return bytes.fromhex(hex_str_clean).decode("utf-8", errors="ignore")
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

# === Track UE Sessions ===
ue_sessions = {}

def normalize_identity(imsi_or_suci):
    """Turn a SUCI into its associated IMSI string (e.g., suci -> imsi if possible)"""
    if imsi_or_suci.startswith("suci-"):
        # You might want to extract the last digits from the SUCI as IMSI mapping
        # Here we make a simple placeholder: treat SUCI as "temporary IMSI"
        return imsi_or_suci  # for now, keep it simple
    return imsi_or_suci

with open(path + input_file, "r") as f:
    packets = json.load(f)

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    tcp = layers.get("tcp", {})
    payload = tcp.get("tcp.payload")
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_epoch", "N/A")
    srcport = int(layers.get("tcp", {}).get("tcp.srcport", 0))
    dstport = int(layers.get("tcp", {}).get("tcp.dstport", 0))

    # Simple direction logic: If srcport > dstport, assume send, otherwise recv
    direction = "send" if srcport > dstport else "recv"

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

                    # Map SUCI and IMSI under same identity if possible
                    # If "supi" field exists inside payload, override SUCI with real IMSI
                    if '"supi":"' in outer_json:
                        match = re.search(r'"supi":"(imsi-\d+)"', outer_json)
                        if match:
                            norm_id = match.group(1)

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

# === Write CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "direction", "imsi", "event", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    # ✅ Write header once
    writer.writeheader()
    
    # ✅ Then loop over sessions
    for imsi, session in ue_sessions.items():
        writer.writerow({
            "frame_number": session["start_frame"],
            "timestamp": f"{session['start_time']:.9f}",
            "direction": session["start_direction"],
            "imsi": imsi,
            "event": "start",
            "decoded_payload": session["start_payload"]
        })
        writer.writerow({
            "frame_number": session["end_frame"],
            "timestamp": f"{session['end_time']:.9f}",
            "direction": session["end_direction"],
            "imsi": imsi,
            "event": "end",
            "decoded_payload": session["end_payload"]
        })

print(f"✅ Registration start/end packets written to {output_csv}")
