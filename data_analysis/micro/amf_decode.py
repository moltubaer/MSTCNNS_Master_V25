import json
import re
import csv

# Set paths
path = "/home/alexandermoltu/pcap_captures/linear/core/100-open5gs-2025.04.25_13.07.15/"
input_file = "amf1.json"
output_csv = input_file + "_registration_events.csv"

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
                            "start_payload": outer_json,
                            "end_frame": int(frame_number),
                            "end_time": float(timestamp),
                            "end_payload": outer_json
                        }
                    else:
                        # Update end frame each time
                        ue_sessions[norm_id]["end_frame"] = int(frame_number)
                        ue_sessions[norm_id]["end_time"] = float(timestamp)
                        ue_sessions[norm_id]["end_payload"] = outer_json

# === Write CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["frame_number", "timestamp", "imsi", "event", "decoded_payload"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for imsi, session in ue_sessions.items():
        # Write start packet
        writer.writerow({
            "frame_number": session["start_frame"],
            "timestamp": f"{session['start_time']:.9f}",
            "imsi": imsi,
            "event": "start",
            "decoded_payload": session["start_payload"]
        })
        # Write end packet
        writer.writerow({
            "frame_number": session["end_frame"],
            "timestamp": f"{session['end_time']:.9f}",
            "imsi": imsi,
            "event": "end",
            "decoded_payload": session["end_payload"]
        })

print(f"✅ Registration start/end packets written to {output_csv}")
