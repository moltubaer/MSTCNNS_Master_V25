import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def collect_nf_data_by_ue_count(input_dir):
    nf_data = {}  # {(ue_count, nf_name): total_processing_time}

    for file in os.listdir(input_dir):
        if file.endswith(".csv") and "_ue_reg" in file:
            df = pd.read_csv(os.path.join(input_dir, file))
            ue_count = len(df)
            nf_name = file.split("_")[0].upper()
            key = (ue_count, nf_name)

            nf_data[key] = nf_data.get(key, 0) + df["delta_ms"].sum()

    return nf_data

def plot_stacked_nf_bars(nf_data, output_path):
    # Prepare data
    ue_counts = sorted(set(k[0] for k in nf_data))
    nf_names = sorted(set(k[1] for k in nf_data))

    # Prepare stacked bar data
    stacks = {nf: [] for nf in nf_names}
    for ue_count in ue_counts:
        for nf in nf_names:
            stacks[nf].append(nf_data.get((ue_count, nf), 0))

    x = np.arange(len(ue_counts))
    bar_width = 0.6
    bottom = np.zeros(len(ue_counts))

    plt.figure(figsize=(10, 6))

    max_total_height = 0

    for nf in nf_names:
        values = np.array(stacks[nf])
        plt.bar(x, values, width=bar_width, bottom=bottom, label=nf)

        # Add text labels inside/above bars
        for i in range(len(values)):
            if values[i] > 0:
                y_pos = bottom[i] + values[i] / 2
                label_pos = bottom[i] + values[i] * 0.5
                # plt.text(x[i], label_pos, nf, ha='center', va='center', fontsize=9, color='white')
        bottom += values
        max_total_height = np.maximum(max_total_height, bottom)

    # Extend Y-axis 10% above tallest stack
    plt.ylim(0, max_total_height.max() * 1.1)

    plt.xticks(x, ue_counts)
    plt.xlabel("Number of UEs")
    plt.ylabel("Total Processing Time (ms)")
    plt.title("Stacked NF Processing Time by UE Count")
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Plot saved to: {output_path}")

def write_data_csv(nf_data, csv_output_path):
    ue_counts = sorted(set(k[0] for k in nf_data))
    nf_names = sorted(set(k[1] for k in nf_data))

    rows = []
    for ue_count in ue_counts:
        row = {"UE Count": ue_count}
        total = 0

        # Calculate total processing time
        for nf in nf_names:
            value = nf_data.get((ue_count, nf), 0)
            row[nf] = value
            total += value

        row["Total"] = total

        # Add percentage per NF
        for nf in nf_names:
            pct = (row[nf] / total * 100) if total > 0 else 0
            row[f"{nf} %"] = round(pct, 2)

        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(csv_output_path, index=False)
    print(f"Data written to CSV: {csv_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot NF processing time grouped by UE count.")
    parser.add_argument("--input", default="./parsed_csv", help="Directory containing parsed CSV files from NFs.")
    parser.add_argument("--output", default="./plots", help="Path to save the output plot.")
    parser.add_argument("--name", required=True, type=str)
    args = parser.parse_args()

    data = collect_nf_data_by_ue_count(args.input)
    plot_stacked_nf_bars(data, f'{args.output}/{args.name}.png')
    write_data_csv(data, f'{args.output}/{args.name}.csv')
