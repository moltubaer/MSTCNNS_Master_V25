import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

files = {
    "Authentication": "tmp/authentication_summary.csv",
    "Deregistration (Context Release)": "tmp/deregistration_(context_release)_summary.csv",
    "Initial Context Setup": "tmp/initial_context_setup_summary.csv",
    "Registration Phase": "tmp/registration_phase_summary.csv"
}

for label, filepath in files.items():
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        continue

    df = pd.read_csv(filepath)
    df["num_ues"] = pd.to_numeric(df["num_ues"], errors="coerce")
    df["total_duration"] = pd.to_numeric(df["total_duration"], errors="coerce")
    df["average_latency"] = pd.to_numeric(df["average_latency"], errors="coerce")
    df.dropna(subset=["num_ues", "total_duration", "average_latency"], inplace=True)

    # Plot total duration
    if "sum_latencies" in df.columns:
        df["sum_latencies"] = pd.to_numeric(df["sum_latencies"], errors="coerce")

    # Combined plot: total_duration + sum_latencies
    plt.figure(figsize=(8, 5))
    plt.plot(df["num_ues"], df["total_duration"], marker="o", label="Total Duration", color="blue")
    
    if "sum_latencies" in df.columns:
        plt.plot(df["num_ues"], df["sum_latencies"], marker="s", linestyle="--", label="Sum of Latencies", color="green")

    plt.title(f"Total Duration & Sum of Latencies vs Number of UEs — {label}")
    plt.xlabel("Number of UEs")
    plt.ylabel("Time (s)")
    plt.grid(True)
    plt.legend()
    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.4f'))
    plt.tight_layout()
    plt.savefig(f"plots/{label.lower().replace(' ', '_')}_combined_duration.png")
    plt.close()


    # Plot average latency
    plt.figure(figsize=(8, 5))
    plt.plot(df["num_ues"], df["average_latency"], marker="o", color="orange", label="Average Latency")
    plt.title(f"Average Latency vs Number of UEs — {label}")
    plt.xlabel("Number of UEs")
    plt.ylabel("Average Latency (s)")
    plt.grid(True)
    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.6f'))
    # ax.yaxis.set_major_locator(ticker.MultipleLocator(0.0001))  # Finer granularity
    plt.tight_layout()
    plt.savefig(f"plots/{label.lower().replace(' ', '_')}_average_latency.png")
    plt.close()

print("✅ Plots saved as PNG files.")
