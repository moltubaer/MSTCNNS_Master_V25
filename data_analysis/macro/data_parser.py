import os
import re
import pandas as pd
import argparse
from collections import defaultdict

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Parse CSVs by test type, UE count, and 5GC type from folder name")
parser.add_argument("--input", "-i", required=True, type=str, help="Input directory (recursive)")
parser.add_argument("--output", "-o", default="./parsed_csv", type=str, help="Output root directory")
args = parser.parse_args()

input_root = args.input
output_root = args.output
os.makedirs(output_root, exist_ok=True)

# === Extract test type from filename ===
def detect_test_type(filename: str) -> str:
    name = filename.lower()
    if "ue_dereg" in name:
        return "ue_dereg"
    elif "run_ues" in name or "ue_reg" in name:
        return "ue_reg"
    elif "pdu_sessions" in name or "pdu_est" in name:
        return "pdu_est"
    elif "pdu_release" in name or "pdu_rel" in name:
        return "pdu_rel"
    return None

# === Extract UE count from filename ===
def extract_ue_count(filename: str) -> str:
    match = re.match(r"(\d+)", filename)
    return match.group(1) if match else "X"

# === Extract 5GC type from parent directory name ===
def extract_core_type(parent_dir_name: str) -> str:
    name = parent_dir_name.lower()
    for candidate in ["free5gc", "open5gs", "magma", "aether", "oai", "srsran"]:
        if candidate in name:
            return candidate
    return "unknown_core"

# === Collect CSVs into groups by (core, test_type, ue_count) ===
csv_groups = defaultdict(list)

for dirpath, _, filenames in os.walk(input_root):
    parent_dir_name = os.path.basename(dirpath)
    core_type = extract_core_type(parent_dir_name)

    for file in filenames:
        if file.endswith(".csv"):
            test_type = detect_test_type(file)
            ue_count = extract_ue_count(file)
            if test_type and core_type:
                key = (core_type, test_type, ue_count)
                csv_groups[key].append(os.path.join(dirpath, file))

# === Process each group ===
for (core_type, test_type, ue_count), file_list in csv_groups.items():
    results = []

    for file_path in file_list:
        df = pd.read_csv(file_path)

        if {'timestamp', 'type', 'id'}.issubset(df.columns):
            grouped = df.groupby('id')
            for ue_id, group in grouped:
                first_row = group[group['type'] == 'first']
                release_row = group[group['type'] == 'release']

                if not first_row.empty and not release_row.empty:
                    delta = float(release_row['timestamp'].values[0]) - float(first_row['timestamp'].values[0])
                    results.append({'ran_ue_ngap_id': ue_id, 'delta_ms': delta * 1000})
                else:
                    print(f"[SKIP] {ue_id}: missing first or release row (file: {os.path.basename(file_path)})")
        else:
            print(f"[ERROR] Missing required columns in: {file_path}")

    # === Save output ===
    if results:
        output_dir = os.path.join(output_root, core_type, test_type)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{ue_count}.{test_type}.csv")
        pd.DataFrame(results).to_csv(output_path, index=False)
        print(f"[OK] Saved: {output_path}")
    else:
        print(f"[WARN] No valid entries for {test_type} ({ue_count}) [{core_type}]")

print("✅ All done.")
