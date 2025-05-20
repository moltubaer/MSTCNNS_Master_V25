import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
import re
from collections import defaultdict

# === CLI Arguments ===
parser = argparse.ArgumentParser(description="Plot combined sys_mon graphs by operation.")
parser.add_argument("--input", "-i", required=True, help="Input directory containing *_summary.csv files.")
parser.add_argument("--output", "-o", required=True, help="Directory to store generated combined plots.")
args = parser.parse_args()

input_dir = args.input
output_dir = args.output
os.makedirs(output_dir, exist_ok=True)

pretty_names = {
    "ue_reg_pdu": "UE Registration with PDU Session Establishment",
    "ue_reg": "UE Registration",
    "ue_dereg": "UE De-registration",
    "pdu_est": "PDU Session Establishment",
    "pdu_rel": "PDU Session Release",
}

# === Group files by operation ===
files_by_op = defaultdict(dict)

for file in os.listdir(input_dir):
    if file.endswith(".csv"):
        match = re.match(r"(ue_reg|ue_dereg|pdu_est|pdu_rel)_(core|ueransim)_(\w+)_.*?_summary\.csv", file)
        if match:
            op, source, core = match.groups()
            files_by_op[op][source] = os.path.join(input_dir, file)

# === Plot each operation's data ===
for op, sources in files_by_op.items():
    try:
        df_core = pd.read_csv(sources.get("core")) if "core" in sources else None
        df_ue = pd.read_csv(sources.get("ueransim")) if "ueransim" in sources else None

        if df_core is None or df_ue is None:
            print(f"⚠️ Skipping {op}: missing core or ueransim CSV.")
            continue

        for df in [df_core, df_ue]:
            df["input_number"] = df["ue_count"]
        
        op_pretty = pretty_names.get(op, op.replace("_", " ").title())
        core_pretty = "Free5GC" if "free5gc" in sources["core"].lower() else "Open5GS" if "open5gs" in sources["core"].lower() else "Unknown"

        # === Combined Plot: CPU Usage ===
        all_cpu_vals = pd.concat([
            df_core["avg_cpu_total"], df_core["max_cpu_total"],
            df_ue["avg_cpu_total"], df_ue["max_cpu_total"]
        ])
        y_min, y_max = all_cpu_vals.min(), all_cpu_vals.max()

        plt.figure(figsize=(8, 5))
        plt.plot(df_core["input_number"], df_core["avg_cpu_total"], marker='o', label="Avg CPU (core)")
        plt.plot(df_core["input_number"], df_core["max_cpu_total"], marker='o', label="Max CPU (core)")
        plt.plot(df_ue["input_number"], df_ue["avg_cpu_total"], marker='o', label="Avg CPU (ueransim)")
        plt.plot(df_ue["input_number"], df_ue["max_cpu_total"], marker='o', label="Max CPU (ueransim)")
        plt.ylim(y_min * 0.95, y_max * 1.05)
        plt.xlabel("Number of UEs")
        plt.ylabel("CPU Usage (%)")
        plt.title(f"{core_pretty} - {op_pretty} - CPU Usage")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{op}_cpu_usage.png"))
        plt.close()

        # === Separate CPU plots ===
        for source, df in [("core", df_core), ("ueransim", df_ue)]:
            plt.figure(figsize=(8, 5))
            plt.plot(df["input_number"], df["avg_cpu_total"], marker='o', label=f"Avg CPU ({source})")
            plt.plot(df["input_number"], df["max_cpu_total"], marker='o', label=f"Max CPU ({source})")
            plt.xlabel("Number of UEs")
            plt.ylabel("CPU Usage (%)")
            plt.title(f"{core_pretty} - {op_pretty} - CPU Usage ({source})")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{op}_cpu_usage_{source}.png"))
            plt.close()

        # === Combined Plot: Memory MB ===
        all_mem_vals = pd.concat([
            df_core["avg_mem_used_mb"], df_core["max_mem_used_mb"],
            df_ue["avg_mem_used_mb"], df_ue["max_mem_used_mb"]
        ])
        plt.figure(figsize=(8, 5))
        plt.plot(df_core["input_number"], df_core["avg_mem_used_mb"], marker='o', label="Avg Mem MB (core)")
        plt.plot(df_core["input_number"], df_core["max_mem_used_mb"], marker='o', label="Max Mem MB (core)")
        plt.plot(df_ue["input_number"], df_ue["avg_mem_used_mb"], marker='o', label="Avg Mem MB (ueransim)")
        plt.plot(df_ue["input_number"], df_ue["max_mem_used_mb"], marker='o', label="Max Mem MB (ueransim)")
        plt.ylim(all_mem_vals.min() * 0.95, all_mem_vals.max() * 1.05)
        plt.xlabel("Number of UEs")
        plt.ylabel("Memory Used (MB)")
        plt.title(f"{core_pretty} - {op_pretty} - Memory Usage")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{op}_memory_usage_mb.png"))
        plt.close()

        # === Separate Memory MB plots ===
        for source, df in [("core", df_core), ("ueransim", df_ue)]:
            plt.figure(figsize=(8, 5))
            plt.plot(df["input_number"], df["avg_mem_used_mb"], marker='o', label=f"Avg Mem MB ({source})")
            plt.plot(df["input_number"], df["max_mem_used_mb"], marker='o', label=f"Max Mem MB ({source})")
            plt.xlabel("Number of UEs")
            plt.ylabel("Memory Used (MB)")
            plt.title(f"{core_pretty} - {op_pretty} - Memory Usage ({source})")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"{op}_memory_usage_mb_{source}.png"))
            plt.close()

        print(f"✅ Plots written for {op}")
    except Exception as e:
        print(f"❌ Error plotting {op}: {e}")
