import json
import argparse
import csv
import os
from collections import defaultdict


num = 100
# Argument parser for optional input file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-f", "--file",
    type=str,
    # default="./captures/pdu-est-re.json",
    default="/home/ubuntu/pcap_captures/" + str(num) + ".json",
    help="Path to the input JSON file"
)
args = parser.parse_args()

with open(args.file) as f:
    data = json.load(f)

# === Helper Functions ===
def get_ue_ids(pkt):
    ids = []
    if "RAN_UE_NGAP_ID" in pkt:
        if isinstance(pkt["RAN_UE_NGAP_ID"], list):
            ids.extend(pkt["RAN_UE_NGAP_ID"])
        else:
            ids.append(pkt["RAN_UE_NGAP_ID"])
    return ids

# === Message Pairs to Match ===
message_pairs = [
    ("0x56", "0x57", "Authentication"),
    ("0x41", "0x43", "Registration"),
    ("0x45", "0x46", "Deregistration (UE)"),
    ("0x47", "0x48", "Deregistration (NW)"),
    ("InitialContextSetup", "InitialContextSetup", "Initial Context Setup"),
    ("PDUSessionResourceSetup", "PDUSessionResourceSetup", "PDU Session Setup"),
    ("UEContextReleaseCommand", "UEContextReleaseComplete", "Deregistration (Context Release)"),
    ("0x41", "InitialContextSetup", "Registration Phase"),
]

# === Extract and Classify Messages ===
ue_packets = defaultdict(list)

for pkt in data:
    ue_ids = get_ue_ids(pkt)
    for ue_id in ue_ids:
        new_pkt = pkt.copy()
        new_pkt["ue_id"] = ue_id
        ue_packets[ue_id].append(new_pkt)

# === Match Messages ===
csv_rows = []

for request_type, response_type, label in message_pairs:
    for ue_id, packets in ue_packets.items():
        req_time = None
        for pkt in packets:
            time = pkt.get("relative")
            nas_msg = pkt.get("NAS_msg_type")
            ngap_proc = pkt.get("ngap_procedure")

            is_request = nas_msg == request_type or ngap_proc == request_type
            is_response = nas_msg == response_type or ngap_proc == response_type

            if is_request:
                req_time = time
            elif is_response and req_time is not None:
                latency = float(time) - float(req_time)
                csv_rows.append({
                    "ue_id": ue_id,
                    "timestamp": req_time,
                    "event_type": label,
                    "latency": latency
                })
                req_time = None

# === Group by Event Type ===
grouped_csv_rows = defaultdict(list)
for row in csv_rows:
    grouped_csv_rows[row["event_type"]].append(row)

# === Write Per-Event CSVs and Summary ===
for event_type, rows in grouped_csv_rows.items():
    timestamps = [float(row["timestamp"]) for row in rows]
    latencies = [float(row["latency"]) for row in rows]

    if not timestamps or not latencies:
        continue

    start_time = min(timestamps)
    end_time = max([t + l for t, l in zip(timestamps, latencies)])
    total_duration = end_time - start_time
    average_latency = sum(latencies) / len(latencies)
    sum_all_latencies = sum(latencies)
    effective_num_ues = len(latencies)

    print(f"📊 {event_type}:")
    print(f"   Total time from first request to last response: {total_duration:.6f}s")
    print(f"   Average UE latency: {average_latency:.6f}s")
    print(f"   Sum of UE latencies: {sum_all_latencies:.6f}s")
    print(f"   Number of matched UEs: {effective_num_ues}\n")

    # Write detailed CSV
    filename = f"{event_type.lower().replace(' ', '_')}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ue_id", "timestamp", "event_type", "latency"])
        writer.writeheader()
        writer.writerows(rows)

    # Write summary CSV
    summary_filename = f"{event_type.lower().replace(' ', '_')}_summary.csv"
    write_header = not os.path.exists(summary_filename) or os.stat(summary_filename).st_size == 0
    with open(summary_filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event_type", "total_duration", "average_latency", "num_ues", "effective_num_ues", "sum_latencies"])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "event_type": event_type,
            "total_duration": f"{total_duration:.6f}",
            "average_latency": f"{average_latency:.6f}",
            "num_ues": num,
            "effective_num_ues": effective_num_ues,
            "sum_latencies": f"{sum_all_latencies:.6f}"
        })
    print(f"📄 Summary written to {summary_filename}")
