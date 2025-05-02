import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv

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
            label = os.path.splitext(file_name)[0]

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
    plt.ylabel("Processing Time (ms)")
    plt.title("Box Plot of Operation Latency Across 5G Core Networks")
    plt.grid(True)
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
    parser.add_argument("--dir", default="./parsed_csv", help="Path to directory with CSVs.")
    parser.add_argument("--mode", choices=["auto", "core"], default="auto", help="Label strategy.")
    parser.add_argument("--output", default="box_plot.png", help="Output PNG filename.")
    args = parser.parse_args()

    core_data = load_data(args.dir, args.mode)
    
    output_dir = "./plots/"

    if not core_data:
        print("No valid data found. Check your CSV files and label mode.")
    else:
        plot_box(core_data, args.output)
        stats_csv_path = os.path.join(output_dir, os.path.splitext(args.output)[0] + ".csv")
        write_stats_csv(core_data, stats_csv_path)
        print(f"Stats written to {stats_csv_path}")
