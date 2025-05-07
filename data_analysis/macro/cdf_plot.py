import os
import re
import csv
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_cdf(data, label, show_percentiles=True):
    sorted_data = np.sort(data)
    yvals = np.arange(1, len(sorted_data) + 1) / float(len(sorted_data))
    plt.plot(sorted_data, yvals, label=label)

    # if show_percentiles:
    #     p50 = np.percentile(sorted_data, 50)
    #     p90 = np.percentile(sorted_data, 90)

    #     plt.axvline(p50, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    #     plt.axvline(p90, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    #     plt.text(p50, 0.05, f"P50: {p50:.1f} ms", rotation=90, verticalalignment='bottom', color='gray')
    #     plt.text(p90, 0.15, f"P90: {p90:.1f} ms", rotation=90, verticalalignment='bottom', color='gray')

def main(dir, mode):
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
                continue  # Skip files that don't match known cores
        else:  # mode == "filename"
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

    if not core_data:
        print("No valid data found. Check directory and label mode.")
        return

    # Plot CDFs
    plt.figure(figsize=(10, 6))
    for label, data in core_data.items():
        if data:
            plot_cdf(data, label)

    plt.xlabel("Processing Time (ms)", fontsize=14)
    plt.ylabel("Cumulative Probability", fontsize=14)
    plt.title(name)
    plt.legend()
    plt.grid(True)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.xlim(left=0)  # Ensures x-axis starts at 0
    plt.tight_layout()
    # After plt.tight_layout()
    plt.savefig(f"{output_path}/{output_basename}.png")

    # Save percentiles to CSV
    write_percentiles_csv(core_data, f"{output_path}/{output_basename}.csv")

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot CDFs of delta_ms values from parsed CSVs.")
    parser.add_argument("--dir", default="./parsed_csv")
    parser.add_argument("--mode", choices=["auto", "core"], default="auto",)
    args = parser.parse_args()

    name = "Open5GS UERANSIM - UE Deregistration"
    output_basename = "open5gs_ue_dereg_cdf"
    output_path = "./plots"

    main(args.dir, args.mode)
