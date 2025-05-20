from collections import defaultdict
import pandas as pd
import os
import argparse
import re

parser = argparse.ArgumentParser(description="Summarize system monitoring CSVs by operation type and source (ueransim/core).")
parser.add_argument("--input", "-i", required=True, help="Input root directory to search for *system.csv files.")
parser.add_argument("--output", "-o", required=True, help="Output directory to store summary CSVs.")
args = parser.parse_args()

input_root = args.input
output_root = args.output
os.makedirs(output_root, exist_ok=True)

summaries_by_key = defaultdict(list)

def extract_info(folder_name, parent_path):
    name = folder_name.lower()
    op_match = re.search(r'(ue_reg_pdu|ue_reg|ue_dereg|pdu_est|pdu_rel)', name)
    op = op_match.group(1) if op_match else "unknown"
    core_type = "ueransim" if "ueransim" in name else "core"
    core_name = os.path.basename(parent_path).lower()
    return op, core_type, core_name

def extract_ue_count(name):
    # Match formats like: "100_UEs_" or "100_linear_" or "100-UEs"
    match = re.match(r'^(\d+)[_-](?:ues|linear)', name.lower())
    return int(match.group(1)) if match else None

for root, _, files in os.walk(input_root):
    for file in files:
        if file.endswith("system.csv"):
            input_path = os.path.join(root, file)
            folder_name = os.path.basename(root)
            rel_path = os.path.relpath(input_path, input_root)

            parent_path = os.path.dirname(root)
            op, core_type, core_name = extract_info(folder_name, parent_path)
            ue_count = extract_ue_count(folder_name)

            try:
                df = pd.read_csv(input_path)

                summary = {
                    "input_file": rel_path,
                    "ue_count": ue_count,
                    "operation": op,
                    "avg_cpu_total": round(df["cpu_total"].mean(), 2),
                    "max_cpu_total": round(df["cpu_total"].max(), 2),
                    "avg_mem_used_mb": round(df["mem_used_mb"].mean(), 2),
                    "max_mem_used_mb": round(df["mem_used_mb"].max(), 2),
                    "avg_mem_percent": round(df["mem_percent"].mean(), 2),
                    "max_mem_percent": round(df["mem_percent"].max(), 2)
                }

                summaries_by_key[(op, core_type, core_name)].append(summary)

            except Exception as e:
                print(f"⚠️ Skipped {input_path}: {e}")

# Write CSVs per (operation, source_type)
for (op, core_type, core_name), entries in summaries_by_key.items():
    df = pd.DataFrame(entries)
    out_path = os.path.join(output_root, f"{op}_{core_type}_{core_name}_summary.csv")
    df.to_csv(out_path, index=False)
    print(f"✅ Saved {len(df)} entries to {out_path}")
