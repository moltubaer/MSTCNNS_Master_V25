import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

PRETTY_NAMES = {
    "core": {
        "open5gs": "Open5GS",
        "free5gc": "Free5GC",
        "aether": "Aether"
    },
    "operation": {
        "ue_reg": "UE Registration",
        "ue_reg_pdu": "UE Registration with PDU Session Establishment",
        "ue_dereg": "UE Deregistration",
        "pdu_est": "PDU Session Establishment",
        "pdu_rel": "PDU Session Release"
    }
}

def parse_folder_metadata(folder_name):
    folder_name = folder_name.lower()
    parts = folder_name.split("_")

    # Extract core (open5gs, free5gc, etc.) by checking known names
    known_cores = ["open5gs", "free5gc", "magma", "aether"]
    core = next((c for c in known_cores if c in parts), "unknown")

    # Extract operation based on keyword in folder name
    if "ue_reg_pdu" in folder_name:
        operation = "ue_reg_pdu"
    elif "ue_reg" in folder_name:
        operation = "ue_reg"
    elif "ue_dereg" in folder_name:
        operation = "ue_dereg"
    elif "pdu_est" in folder_name:
        operation = "pdu_est"
    elif "pdu_rel" in folder_name:
        operation = "pdu_rel"
    else:
        operation = "unknown"

    # Use the first number-like part as test number (e.g., 100)
    test_number = next((p for p in parts if p.isdigit()), "0")

    return test_number, operation, core

def collect_nf_data_from_folder(folder_path, test_number):
    nf_data = {}
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            full_path = os.path.join(folder_path, file)
            df = pd.read_csv(full_path)
            nf_name = file.split("_")[1].split(".")[0].upper()  # e.g., amf.pdml.csv -> AMF
            key = (test_number, nf_name)
            nf_data[key] = nf_data.get(key, 0) + df["delta_ms"].sum()
    return nf_data

def plot_stacked_nf_bars(nf_data, output_path, title):
    ue_counts = sorted(set(k[0] for k in nf_data))
    nf_names = sorted(set(k[1] for k in nf_data))

    stacks = {nf: [] for nf in nf_names}
    for ue_count in ue_counts:
        for nf in nf_names:
            stacks[nf].append(nf_data.get((ue_count, nf), 0))

    x = np.arange(len(ue_counts))
    bar_width = 0.6
    bottom = np.zeros(len(ue_counts))

    plt.figure(figsize=(10, 6))

    max_total_height = np.zeros(len(ue_counts))
    added_labels = set()
    plotted_any = False

    for nf in nf_names:
        values = np.array(stacks[nf])
        if values.sum() > 0:
            label = nf if nf not in added_labels else None
            plt.bar(x, values, width=bar_width, bottom=bottom, label=label)
            added_labels.add(nf)
            bottom += values
            max_total_height = np.maximum(max_total_height, bottom)
            plotted_any = True

    if not plotted_any:
        print(f"Skipping empty plot: {title}")
        plt.close()
        return

    plt.xticks(x, ue_counts)
    plt.xlabel("Test Number")
    plt.ylabel("Total Processing Time (ms)")
    plt.title(title)
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
        row = {"Test Number": ue_count}
        total = 0
        for nf in nf_names:
            value = nf_data.get((ue_count, nf), 0)
            row[nf] = value
            total += value
        row["Total"] = total
        for nf in nf_names:
            pct = (row[nf] / total * 100) if total > 0 else 0
            row[f"{nf} %"] = round(pct, 2)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(csv_output_path, index=False)
    print(f"Data written to CSV: {csv_output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatically generate NF plots per operation/core.")
    parser.add_argument("--input", "-i", required=True, help="Root input directory containing test folders.")
    parser.add_argument("--output", "-o", default="./plots", help="Output directory for plots and CSVs.")
    args = parser.parse_args()

    groups = defaultdict(list)  # (operation, core) -> list of (folder_path, test_number)

    for root, dirs, _ in os.walk(args.input):
        for d in dirs:
            parsed = parse_folder_metadata(d)
            if parsed:
                test_number, operation, core = parsed
                groups[(operation, core)].append((os.path.join(root, d), test_number))

    os.makedirs(args.output, exist_ok=True)

    for (operation, core), folder_info in groups.items():
        combined_data = {}
        for folder_path, test_number in folder_info:
            nf_data = collect_nf_data_from_folder(folder_path, test_number)
            for key, value in nf_data.items():
                combined_data[key] = combined_data.get(key, 0) + value

        pretty_core = PRETTY_NAMES["core"].get(core.lower(), core.capitalize())
        pretty_op = PRETTY_NAMES["operation"].get(operation.lower(), operation.replace("_", " ").title())
        basename = f"{pretty_core} - {pretty_op}".replace(" ", "_")

        plot_path = os.path.join(args.output, f"{basename}.png")
        csv_path = os.path.join(args.output, f"{basename}.csv")
        title = f"{pretty_core} - {pretty_op}"

        plot_stacked_nf_bars(combined_data, plot_path, title)
        write_data_csv(combined_data, csv_path)
