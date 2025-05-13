import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv
import re

def load_data(dir, mode):
    core_labels = {
        "open5gs": "Open5GS",
        "magma": "MagmaCore",
        "free5gc": "Free5GC"
    }

    core_data = {}

    for file_name in os.listdir(dir):
        if not file_name.endswith(".csv"):
            continue

        file_path = os.path.join(dir, file_name)
        label = None

        if mode == "core":
            for key in core_labels:
                if key in file_name.lower():
                    label = core_labels[key]
                    break
            if not label:
                continue  # skip unknown cores
        else:  # 'filename' mode
            label = re.match(r"^(\d+)", file_name)
            if label:
                label = label.group(1)
            else:
                label = "X"
                # label = os.path.splitext(file_name)[0]

        df = pd.read_csv(file_path)
        if 'delta_ms' in df.columns:
            if label not in core_data:
                core_data[label] = []
            core_data[label].extend(df['delta_ms'].dropna().tolist())

    return core_data

def plot_box(core_data, output_path):
    labels = list(core_data.keys())
    data = [core_data[label] for label in labels]

    plt.figure(figsize=(10, 6))
    plt.boxplot(data, labels=labels, showmeans=True)
    plt.xlabel("UE Count", fontsize=14)
    plt.ylabel("Processing Time (ms)", fontsize=14)
    plt.title("Box Plot of Operation Latency Across 5G Core Networks")
    plt.title(name)
    plt.grid(True)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(bottom=0)
    # plt.ylim(top=40)

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    full_output_path = os.path.join(output_dir, output_path)
    plt.savefig(full_output_path)
    print(f"Box plot saved to {full_output_path}")

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a box plot of delta_ms values from parsed CSVs.")
    parser.add_argument("--input", "-i", default="./parsed_csv", type=str)
    parser.add_argument("--mode", "-m", choices=["auto", "core"], default="auto")
    parser.add_argument("--output", "-o", default="./plots", type=str)
    parser.add_argument("--name", "-n", required=True, type=str)
    args = parser.parse_args()

    core = "Open5GS"
    # core = "Free5GC"
    
    operation = "UE Registration"
    # operation = "UE Deregistration"
    # operation = "PDU Session Establishment"
    # operation = "PDU Session Release"
    
    name = f'{core} - {operation}'

    output_dir = args.output
    
    core_data = load_data(args.input, args.mode)

    if not core_data:
        print("No valid data found. Check your CSV files and label mode.")
    else:
        plot_box(core_data, args.name)
        stats_csv_path = os.path.join(output_dir, os.path.splitext(args.name)[0] + ".csv")
        write_stats_csv(core_data, stats_csv_path)
        print(f"Stats written to {stats_csv_path}")
