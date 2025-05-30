import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np
import os

from matplotlib.lines import Line2D

def parse_title_and_output_from_filename(filepath, input_root, output_root):
    base = os.path.basename(filepath)
    name, _ = os.path.splitext(base)
    parts = name.split('_')

    if len(parts) < 6:
        title = "Time Series Dot Plot"
    else:
        num_ues = parts[0]
        framework = parts[1].capitalize()
        interval = parts[3]
        action = parts[4:6]

        try:
            interval_ms = int(float(interval) * 1000)
        except ValueError:
            interval_ms = interval

        action_map = {
            ('ue', 'reg'): "UE Registration",
            ('ue', 'dereg'): "UE Deregistration",
            ('ue', 'reg_pdu'): "UE Registration With PDU Session Establishment",
            ('ue', 'dereg_pdu'): "UE Deregistration With PDU Session Release"
        }
        action_label = action_map.get(tuple(action), ' '.join(map(str.capitalize, action)))
        title = f"{framework} - {action_label} - {num_ues} UEs - {interval_ms} ms"

    # Correct relative output path
    rel_path = os.path.relpath(filepath, start=input_root)
    rel_dir = os.path.dirname(rel_path)
    output_dir = os.path.join(output_root, rel_dir)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{name}_plot.png")

    return title, output_file

def plot_csv(input_file, output_file, title):
    df = pd.read_csv(input_file)
    df_sorted = df.sort_values(by='timestamp').reset_index(drop=True)

    jitter_y = np.random.uniform(-0.1, 0.1, size=len(df_sorted))
    x = df_sorted['timestamp'].tolist()
    y = jitter_y.tolist()
    types = df_sorted['type'].fillna('').tolist()

    colors = []
    has_first = has_release = has_other = False

    for t in types:
        if t == 'first':
            colors.append('green')
            has_first = True
        elif t == 'release':
            colors.append('red')
            has_release = True
        else:
            colors.append('purple')
            has_other = True

    fig, ax = plt.subplots(figsize=(12, 3))
    ax.plot(x, y, color='gray', linewidth=1, alpha=0.6)
    ax.scatter(x, y, c=colors, alpha=0.7, s=10)

    ax.set_yticks([])
    ax.set_xlabel('Timestamp (s)')
    ax.set_title(title)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    legend_elements = []
    if has_first:
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label='first',
                                      markerfacecolor='green', markersize=6))
    if has_release:
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label='release',
                                      markerfacecolor='red', markersize=6))
    if has_other:
        legend_elements.append(Line2D([0], [0], marker='o', color='w', label='other',
                                      markerfacecolor='purple', markersize=6))

    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.25),
              ncol=len(legend_elements), frameon=False)

    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    print(f"Saved plot to: {output_file}")

def process_directory(input_dir, output_dir):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.csv'):
                input_path = os.path.join(root, file)
                title, output_path = parse_title_and_output_from_filename(input_path, input_dir, output_dir)
                try:
                    plot_csv(input_path, output_path, title)
                except Exception as e:
                    print(f"Error processing {input_path}: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch process CSVs into time series dot plots.')
    parser.add_argument('--input', '-i', default='./input', help='Input directory with CSV files')
    parser.add_argument('--output', '-o', default='./output', help='Output directory for PNG plots')

    args = parser.parse_args()
    process_directory(args.input, args.output)
