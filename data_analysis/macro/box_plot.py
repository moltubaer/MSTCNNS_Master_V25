import os
import re
import csv
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

CORE_NAME_MAP = {
    "open5gs": "Open5GS",
    "free5gc": "Free5GC",
    "aether": "ONF Aether",
}

OP_NAME_MAP = {
    "ue_reg_pdu": "UE Registration with PDU Session Establishment",
    "ue_reg": "UE Registration",
    "ue_dereg": "UE Deregistration",
    "pdu_est": "PDU Session Establishment",
    "pdu_rel": "PDU Session Release",
    # "pdu_release": "PDU Session Release",
    # "pdu_sessions": "PDU Session Establishment",
    # "run_ues": "UE Registration",
}

def load_grouped_data(csv_files):
    core_data = {}
    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        match = re.match(r"^(\d+)", filename)
        label = match.group(1) if match else "X"

        df = pd.read_csv(csv_path)
        if 'delta_ms' in df.columns:
            core_data.setdefault(label, []).extend(df['delta_ms'].dropna().tolist())
    return core_data

def plot_box(core_data, title, output_img):
    labels = sorted(core_data.keys())
    data = [core_data[label] for label in labels]

    plt.figure(figsize=(10, 6))
    plt.boxplot(data, labels=labels, showmeans=True)
    plt.xlabel("UE Count", fontsize=14)
    plt.ylabel("Processing Time (ms)", fontsize=14)
    plt.title(title)
    plt.grid(True)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(output_img)
    plt.close()
    print(f"[OK] Box plot saved: {output_img}")

def write_stats_csv(core_data, output_path_csv):
    with open(output_path_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Label', 'Count', 'Min', 'Max', 'Mean', 'Median', 'P90', 'Outliers', 'Outlier %'])
        for label, data in core_data.items():
            if data:
                arr = np.array(data)
                q1 = np.percentile(arr, 25)
                q3 = np.percentile(arr, 75)
                iqr = q3 - q1
                upper_bound = q3 + 1.5 * iqr
                outliers = np.sum(arr > upper_bound)
                outlier_pct = (outliers / len(arr)) * 100
                writer.writerow([
                    label,
                    len(arr),
                    f"{np.min(arr):.3f}",
                    f"{np.max(arr):.3f}",
                    f"{np.mean(arr):.3f}",
                    f"{np.median(arr):.3f}",
                    f"{np.percentile(arr, 90):.3f}",
                    outliers,
                    f"{outlier_pct:.2f}"
                ])
    print(f"[OK] Stats saved: {output_path_csv}")

def main(input_root, output_root):
    for core_name in os.listdir(input_root):
        core_path = os.path.join(input_root, core_name)
        if not os.path.isdir(core_path):
            continue

        for op_name in os.listdir(core_path):
            op_path = os.path.join(core_path, op_name)
            if not os.path.isdir(op_path):
                continue

            csv_files = [
                os.path.join(op_path, f)
                for f in os.listdir(op_path)
                if f.endswith(".csv")
            ]
            if not csv_files:
                continue

            # Load and process data
            core_data = load_grouped_data(csv_files)
            if not core_data:
                print(f"[SKIP] No valid data in {op_path}")
                continue

            # Output
            out_dir = os.path.join(output_root, core_name)
            os.makedirs(out_dir, exist_ok=True)

            core_title = CORE_NAME_MAP.get(core_name.lower(), core_name)
            op_title = OP_NAME_MAP.get(op_name.lower(), op_name.replace("_", " ").title())
            title = f"{core_title} - {op_title}"
            out_base = f"{core_name}_{op_name}_box".lower()
            out_img = os.path.join(out_dir, f"{out_base}.png")
            out_csv = os.path.join(out_dir, f"{out_base}.csv")

            # Plot and stats
            plot_box(core_data, title, out_img)
            write_stats_csv(core_data, out_csv)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-plot boxplots from structured delta_ms CSVs")
    parser.add_argument("--input", "-i", default="./parsed_csv", type=str)
    parser.add_argument("--output", "-o", default="./plots", type=str)
    args = parser.parse_args()

    main(args.input, args.output)
