import json
import csv

# amf

# === Paths ===
path = "/home/alexandermoltu/pcap_captures/full_test_core/ue_dereg/100-open5gs-2025.04.28_12.33.12/"
input_file = "amf.json"
output_csv = input_file + "_matched_frames.csv"

# === Recursive helper to find RAN_UE_NGAP_ID ===
def extract_ran_ue_ngap_id(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "ngap.RAN_UE_NGAP_ID":
                return value
            result = extract_ran_ue_ngap_id(value)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = extract_ran_ue_ngap_id(item)
            if result is not None:
                return result
    return None

# === Recursive helper to detect UEContextReleaseCommand ===
def detect_release_command(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "ngap.procedureCode" and value == "41":
                return True
            if detect_release_command(value):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if detect_release_command(item):
                return True
    return False

# === Main Processing ===
matched_frames = {}

with open(path + input_file, "r") as f:
    packets = json.load(f)

print(f"🔎 Loaded {len(packets)} packets.")

for pkt in packets:
    layers = pkt.get("_source", {}).get("layers", {})
    ngap = layers.get("ngap", {})
    frame_number = layers.get("frame", {}).get("frame.number", "N/A")
    timestamp = layers.get("frame", {}).get("frame.time_epoch", "N/A")

    if not ngap:
        continue

    ran_ue_ngap_id = extract_ran_ue_ngap_id(ngap)

    if ran_ue_ngap_id:
        print(f"➡️ Found RAN_UE_NGAP_ID={ran_ue_ngap_id} at frame {frame_number}")

    if not ran_ue_ngap_id:
        continue

    # First appearance
    if ran_ue_ngap_id not in matched_frames:
        matched_frames[ran_ue_ngap_id] = {"first": (frame_number, timestamp), "release": None}
        print(f"📥 First packet for UE {ran_ue_ngap_id} at frame {frame_number}, timestamp {timestamp}")

    # Detect release command
    if detect_release_command(ngap):
        matched_frames[ran_ue_ngap_id]["release"] = (frame_number, timestamp)
        print(f"📤 Release command for UE {ran_ue_ngap_id} at frame {frame_number}, timestamp {timestamp}")

# === Write CSV ===
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["ran_ue_ngap_id", "frame_number", "timestamp", "type"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for ran_ue_ngap_id, frames in matched_frames.items():
        first = frames.get("first")
        release = frames.get("release")
        if first:
            writer.writerow({
                "ran_ue_ngap_id": ran_ue_ngap_id,
                "frame_number": first[0],
                "timestamp": first[1],
                "type": "first"
            })
        if release:
            writer.writerow({
                "ran_ue_ngap_id": ran_ue_ngap_id,
                "frame_number": release[0],
                "timestamp": release[1],
                "type": "release"
            })

print(f"✅ Matched frames written to {output_csv}")
