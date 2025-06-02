import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import glob
import csv

def plot_aggregated_cpu(data, outpath):
    plt.figure(figsize=(14, 6))
    plt.fill_between(data['time'], data['cpu_total'], color='skyblue', alpha=0.4)
    plt.plot(data['time'], data['cpu_total'], label='CPU Total', linewidth=2, color='blue')
    plt.xlabel('Timestamp (s)')
    plt.ylabel('CPU Usage (%)')
    plt.title('Aggregated CPU Usage Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()

def plot_all_single_cpus(data, cpu_cols, outpath):
    plt.figure(figsize=(16, 8))
    for cpu_col in cpu_cols:
        plt.plot(data['time'], data[cpu_col], label=cpu_col)
    plt.xlabel('Timestamp (s)')
    plt.ylabel('CPU Usage (%)')
    plt.title('Per-CPU Usage Over Time')
    plt.legend(loc='upper right', ncol=2)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()

def plot_ram(data, outpath):
    plt.figure(figsize=(14, 6))
    plt.plot(data['time'], data['mem_used_mb'], label='Memory Used (MB)', color='purple')
    plt.plot(data['time'], data['mem_percent'], label='Memory Usage (%)', color='orange')
    plt.xlabel('Timestamp (s)')
    plt.ylabel('Memory')
    plt.title('RAM Usage Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()

def cpu_stats(data, column):
    values = data[column].dropna()
    avg = values.mean()
    median = values.median()
    min_val = values.min()
    max_val = values.max()
    p80 = 0.8 * max_val  # 80% of max value
    peaks = values[values > p80].tolist()
    return {
        "average": avg,
        "median": median,
        "min": min_val,
        "max": max_val,
        "p80": p80,
        "peak_values": peaks
    }

def write_stats_to_csv(stats_dict, outpath):
    with open(outpath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['stat', 'value'])
        for key, value in stats_dict.items():
            if key == "peak_values":
                writer.writerow([key, ";".join([f"{v:.3f}" for v in value])])
            else:
                writer.writerow([key, f"{value:.3f}"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CPU and RAM Analysis')
    parser.add_argument('-f','--filepath', type=str, default='./csv_cpu', help='Path to the folder containing CSV files')
    parser.add_argument('-m','--mode', type=str, choices=['aggregated-cpu', 'single-cpu', 'ram'], default='aggregated-cpu',
                        help='Analysis mode: aggregated-cpu, single-cpu, or ram')
    parser.add_argument('-o','--output', type=str, default='./cpu_ram_pngs', help='Output folder for PNG files and stats')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    csv_files = glob.glob(os.path.join(args.filepath, "*.csv"))

    for csv_file in csv_files:
        data = pd.read_csv(csv_file)
        # Convert timestamp to datetime and then to relative seconds
        data['time'] = pd.to_datetime(data['timestamp'], unit='s')
        data['rel_time'] = (data['time'] - data['time'].iloc[0]).dt.total_seconds()
        base_name = os.path.splitext(os.path.basename(csv_file))[0]

        if args.mode == 'aggregated-cpu':
            out_png = os.path.join(args.output, f"{base_name}_{args.mode}.png")
            out_csv = os.path.join(args.output, f"{base_name}_{args.mode}_stats.csv")
            # Use relative time for plotting
            data_plot = data.copy()
            data_plot['time'] = data_plot['rel_time']
            plot_aggregated_cpu(data_plot, out_png)
            stats = cpu_stats(data, "cpu_total")
            write_stats_to_csv(stats, out_csv)
            print(f"[OK] Saved: {out_png} and {out_csv}")
        elif args.mode == 'single-cpu':
            cpu_cols = [col for col in data.columns if col.startswith('cpu') and col != 'cpu_total']
            out_png = os.path.join(args.output, f"{base_name}_allcpus_{args.mode}.png")
            data_plot = data.copy()
            data_plot['time'] = data_plot['rel_time']
            plot_all_single_cpus(data_plot, cpu_cols, out_png)
            print(f"[OK] Saved: {out_png}")
            out_csv = os.path.join(args.output, f"{base_name}_allcpus_{args.mode}_stats.csv")
            with open(out_csv, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['cpu', 'average', 'median', 'min', 'max', 'p80', 'peak_values'])
                for cpu_col in cpu_cols:
                    stats = cpu_stats(data, cpu_col)
                    peak_str = ";".join([f"{v:.3f}" for v in stats["peak_values"]])
                    writer.writerow([
                        cpu_col,
                        f"{stats['average']:.3f}",
                        f"{stats['median']:.3f}",
                        f"{stats['min']:.3f}",
                        f"{stats['max']:.3f}",
                        f"{stats['p80']:.3f}",
                        peak_str
                    ])
            print(f"[OK] Saved: {out_csv}")
        elif args.mode == 'ram':
            out_png = os.path.join(args.output, f"{base_name}_{args.mode}.png")
            out_csv = os.path.join(args.output, f"{base_name}_{args.mode}_stats.csv")
            data_plot = data.copy()
            data_plot['time'] = data_plot['rel_time']
            plot_ram(data_plot, out_png)
            stats = cpu_stats(data, "mem_used_mb")
            write_stats_to_csv(stats, out_csv)
            print(f"[OK] Saved: {out_png} and {out_csv}")
