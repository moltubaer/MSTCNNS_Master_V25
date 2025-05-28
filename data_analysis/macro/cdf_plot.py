import os
import re
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

CORE_NAME_MAP = {
    "open5gs": "Open5GS",
    "free5gc": "Free5GC",
    "aether": "Aether",
}

OP_NAME_MAP = {
    "ue_reg_pdu": "UE Registration with PDU Session Establishment",
    "ue_reg": "UE Registration with PDU Session Establishment",
    "ue_dereg": "UE Deregistration with PDU Session Release",
    "pdu_est": "PDU Session Establishment",
    "pdu_rel": "PDU Session Release",
}

def plot_cdf(data, label, logx=False):
    data = np.array(data)

    # Filter out non-positive values if using log scale
    if logx:
        data = data[data > 0]
        if len(data) == 0:
            print(f"[WARN] All data for {label} is <= 0, skipping.")
            return

    sorted_data = np.sort(data)
    yvals = np.arange(1, len(sorted_data) + 1) / float(len(sorted_data))
    plt.plot(sorted_data, yvals, label=label)

def write_percentiles_csv(core_data, output_path_csv):
    percentiles = [50, 90, 99]
    with open(output_path_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Label', 'p50 (ms)', 'p90 (ms)', 'p99 (ms)'])
        for label, data in core_data.items():
            if data:
                p50 = np.percentile(data, 50)
                p90 = np.percentile(data, 90)
                p99 = np.percentile(data, 99)
                writer.writerow([label, f"{p50:.3f}", f"{p90:.3f}", f"{p99:.3f}"])

def generate_plot(core_dir, op_dir, csv_files, output_root, logx=False):
    core = os.path.basename(core_dir)
    operation = os.path.basename(op_dir)

    core_data = {}

    for csv_path in csv_files:
        filename = os.path.basename(csv_path)
        match = re.match(r"^(\d+)", filename)
        label = match.group(1) if match else "X"

        df = pd.read_csv(csv_path)
        if 'delta_ms' in df.columns:
            core_data.setdefault(label, []).extend(df['delta_ms'].dropna().tolist())

    min_positive = float('inf')
    for data in core_data.values():
        data_array = np.array(data)
        positive_values = data_array[data_array > 0]
        if positive_values.size > 0:
            min_positive = min(min_positive, np.min(positive_values))

    if min_positive == float('inf'):
        min_positive = 0.1  # fallback if no valid data


    if not core_data:
        print(f"[SKIP] No valid data in {op_dir}")
        return

    # === Plot ===
    plt.figure(figsize=(10, 6))
    for label, data in sorted(core_data.items()):
        plot_cdf(data, label, logx=logx)

    plt.xlabel("Processing Time (ms)", fontsize=14)
    plt.ylabel("Cumulative Probability", fontsize=14)
    core_title = CORE_NAME_MAP.get(core.lower(), core.capitalize())
    op_title = OP_NAME_MAP.get(operation.lower(), operation.replace("_", " ").title())
    plt.title(f"{core_title} - {op_title} - {ms} ms", fontsize=15)
    plt.legend(title="UEs")
    plt.grid(True)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xlim(left=0)

    if logx:
        plt.xscale("log")
        plt.xlim(left=min_positive)

    plt.tight_layout()

    # === Output filenames ===
    out_dir = os.path.join(output_root, core)
    os.makedirs(out_dir, exist_ok=True)

    suffix = "_logx" if logx else ""
    out_base = f"{core}_{operation}_cdf{suffix}".lower()
    out_img = os.path.join(out_dir, f"{out_base}.png")
    out_csv = os.path.join(out_dir, f"{out_base}.csv")

    plt.savefig(out_img)
    write_percentiles_csv(core_data, out_csv)
    plt.close()
    print(f"[OK] Plot saved: {out_img}")

def main(input_root, output_root, logx=False):
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
            if csv_files:
                generate_plot(core_path, op_path, csv_files, output_root, logx=logx)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto-plot all CDFs by core and operation")
    parser.add_argument("--input", "-i", default="./parsed_csv", type=str)
    parser.add_argument("--output", "-o", default="./plots", type=str)
    parser.add_argument("--logx", action="store_true", help="Use logarithmic scale for x-axis")
    parser.add_argument("--ms", required=True, type=str)
    args = parser.parse_args()

    ms = args.ms

    main(args.input, args.output, logx=args.logx)
