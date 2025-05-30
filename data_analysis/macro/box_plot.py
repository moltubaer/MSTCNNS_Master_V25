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
    "aether": "Aether",
}

CORE_COLOR_MAP = {
    "aether": "#ea9999",   # soft red (darker than #f4cccc)
    "open5gs": "#9fc5e8",  # soft blue (darker than #cfe2f3)
    "free5gc": "#ffe599",  # soft yellow (darker than #fff2cc)
}

OP_NAME_MAP = {
    "ue_reg_pdu": "UE Registration with PDU Session Establishment",
    "ue_reg": "UE Registration with PDU Session Establishment",
    "ue_dereg": "UE Deregistration with PDU Session Release",
    "pdu_est": "PDU Session Establishment",
    "pdu_rel": "PDU Session Release",
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

def plot_box(core_data, title, output_img, logy=False, core_name=None):
    labels = sorted(core_data.keys())
    data = [core_data[label] for label in labels]
    min_val = min([min(d) for d in data if d]) if logy else 1

    plt.figure(figsize=(10, 6))
    box = plt.boxplot(data, labels=labels, showmeans=True, patch_artist=True)

    # Apply color if core_name is known
    if core_name:
        color = CORE_COLOR_MAP.get(core_name.lower(), "lightgray")
        for patch in box['boxes']:
            patch.set_facecolor(color)

    plt.xlabel("UE Count", fontsize=14)
    plt.ylabel("Processing Time (ms)", fontsize=14)
    plt.title(title)
    plt.grid(True)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    if logy:
        plt.yscale("log")
        plt.ylim(bottom=min_val)
    else:
        plt.ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(output_img)
    plt.close()
    print(f"[OK] Box plot saved: {output_img}")

def plot_grouped_box(core_data_dict, op_title, output_img, logy=False):
    all_ue_counts = sorted(set(ue_count for core in core_data_dict.values() for ue_count in core.keys()))
    all_cores = sorted(core_data_dict.keys())
    data = []
    positions = []
    colors = []
    xtick_labels = []

    group_width = 0.8
    box_width = group_width / len(all_cores)

    for i, ue_count in enumerate(all_ue_counts):
        base_x = i + 1
        for j, core in enumerate(all_cores):
            core_label = CORE_NAME_MAP.get(core.lower(), core)
            color = CORE_COLOR_MAP.get(core.lower(), "gray")
            ue_data = core_data_dict[core].get(str(ue_count), [])
            if ue_data:
                data.append(ue_data)
                pos = base_x - group_width / 2 + j * box_width + box_width / 2
                positions.append(pos)
                colors.append(color)
                xtick_labels.append(f"{ue_count}\n{core_label}")

    min_val = min([min(d) for d in data if d]) if logy else 1

    plt.figure(figsize=(14, 7))
    box = plt.boxplot(
        data,
        positions=positions,
        widths=box_width * 0.9,
        patch_artist=True,
        showmeans=True
    )

    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)

    plt.xlabel("UE Count", fontsize=14)
    plt.ylabel("Processing Time (ms)", fontsize=14)
    plt.title(f"{op_title} - {ms} ms", fontsize=15)
    plt.grid(True, axis='y')

    plt.xticks(ticks=positions, labels=xtick_labels, rotation=90, fontsize=10)
    plt.yticks(fontsize=12)
    if logy:
        plt.yscale("log")
        plt.ylim(bottom=min_val)
    else:
        plt.ylim(bottom=0)

    handles = [plt.Line2D([0], [0], color=CORE_COLOR_MAP[core], lw=4) for core in all_cores if core in CORE_COLOR_MAP]
    labels = [CORE_NAME_MAP.get(core, core) for core in all_cores if core in CORE_COLOR_MAP]
    plt.legend(handles, labels, title="Core", loc="upper right")

    plt.tight_layout()
    plt.savefig(output_img)
    plt.close()
    print(f"[OK] Grouped box plot saved: {output_img}")

def write_stats_csv(core_data, output_path_csv):
    with open(output_path_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Label', 'Count', 'Min', 'Max', 'Mean', 'Median',
            'Q1', 'Q3', 'IQR',
            'Lower Whisker', 'Upper Whisker',
            'Lower Outliers', 'Upper Outliers', 'Total Outliers', 'Outlier %'
        ])
        for label, data in core_data.items():
            if data:
                arr = np.array(data)
                q1 = np.percentile(arr, 25)
                q3 = np.percentile(arr, 75)
                iqr = q3 - q1
                lower_whisker = q1 - 1.5 * iqr
                upper_whisker = q3 + 1.5 * iqr

                lower_outliers = np.sum(arr < lower_whisker)
                upper_outliers = np.sum(arr > upper_whisker)
                total_outliers = lower_outliers + upper_outliers
                outlier_pct = (total_outliers / len(arr)) * 100

                writer.writerow([
                    label,
                    len(arr),
                    f"{np.min(arr):.3f}",
                    f"{np.max(arr):.3f}",
                    f"{np.mean(arr):.3f}",
                    f"{np.median(arr):.3f}",
                    f"{q1:.3f}",
                    f"{q3:.3f}",
                    f"{iqr:.3f}",
                    f"{lower_whisker:.3f}",
                    f"{upper_whisker:.3f}",
                    lower_outliers,
                    upper_outliers,
                    total_outliers,
                    f"{outlier_pct:.2f}"
                ])
    print(f"[OK] Extended stats saved: {output_path_csv}")

# def write_stats_csv(core_data, output_path_csv):
#     with open(output_path_csv, mode='w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Label', 'Count', 'Min', 'Max', 'Mean', 'Median', 'P90', 'Outliers', 'Outlier %'])
#         for label, data in core_data.items():
#             if data:
#                 arr = np.array(data)
#                 q1 = np.percentile(arr, 25)
#                 q3 = np.percentile(arr, 75)
#                 iqr = q3 - q1
#                 upper_bound = q3 + 1.5 * iqr
#                 outliers = np.sum(arr > upper_bound)
#                 outlier_pct = (outliers / len(arr)) * 100
#                 writer.writerow([
#                     label,
#                     len(arr),
#                     f"{np.min(arr):.3f}",
#                     f"{np.max(arr):.3f}",
#                     f"{np.mean(arr):.3f}",
#                     f"{np.median(arr):.3f}",
#                     f"{np.percentile(arr, 90):.3f}",
#                     outliers,
#                     f"{outlier_pct:.2f}"
#                 ])
#     print(f"[OK] Stats saved: {output_path_csv}")

def main(input_root, output_root, grouped=False, logy=False):
    suffix = "_logy" if logy else ""

    if grouped:
        for op_name in OP_NAME_MAP:
            core_data_dict = {}
            for core_name in os.listdir(input_root):
                core_path = os.path.join(input_root, core_name)
                if not os.path.isdir(core_path):
                    continue

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

                core_data = load_grouped_data(csv_files)
                if core_data:
                    core_data_dict[core_name] = core_data

            if not core_data_dict:
                continue

            out_dir = os.path.join(output_root, "comparison")
            os.makedirs(out_dir, exist_ok=True)
            op_title = OP_NAME_MAP.get(op_name, op_name.replace("_", " ").title())
            out_base = f"compare_{op_name}_box{suffix}"
            out_img = os.path.join(out_dir, f"{out_base}.png")
            plot_grouped_box(core_data_dict, op_title, out_img, logy=logy)
    else:
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

                core_data = load_grouped_data(csv_files)
                if not core_data:
                    print(f"[SKIP] No valid data in {op_path}")
                    continue

                out_dir = os.path.join(output_root, core_name)
                os.makedirs(out_dir, exist_ok=True)

                core_title = CORE_NAME_MAP.get(core_name.lower(), core_name)
                op_title = OP_NAME_MAP.get(op_name.lower(), op_name.replace("_", " ").title())
                title = f"{core_title} - {op_title} - {ms} ms"
                out_base = f"{core_name}_{op_name}_box{suffix}".lower()
                out_img = os.path.join(out_dir, f"{out_base}.png")
                out_csv = os.path.join(out_dir, f"{out_base}.csv")

                plot_box(core_data, title, out_img, logy=logy, core_name=core_name)
                write_stats_csv(core_data, out_csv)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-plot boxplots from structured delta_ms CSVs")
    parser.add_argument("--input", "-i", default="./parsed_csv", type=str)
    parser.add_argument("--output", "-o", default="./plots", type=str)
    parser.add_argument("--grouped", action="store_true", help="Enable grouped comparison mode across cores")
    parser.add_argument("--logy", action="store_true", help="Enable logarithmic y-axis for box plots")
    parser.add_argument("--ms", required=True, type=str)
    args = parser.parse_args()

    ms = args.ms

    main(args.input, args.output, grouped=args.grouped, logy=args.logy)