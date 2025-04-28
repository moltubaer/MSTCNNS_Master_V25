import pandas as pd
import re
import argparse

def normalize_identity(identity):
    if identity.startswith("suci-"):
        # Convert suci to imsi-like key (or keep as is)
        return identity.split("-")[-1]  # Take last part (0000000001 etc.)
    if identity.startswith("imsi-"):
        return identity.split("-")[-1]
    return identity

def calculate_processing_times(csv_file):
    df = pd.read_csv(csv_file)

    # Normalize identities to match suci and imsi together
    df["norm_id"] = df["imsi"].apply(normalize_identity)

    results = []

    # Group by normalized ID
    for norm_id, group in df.groupby("norm_id"):
        start_time = group["timestamp"].min()
        end_time = group["timestamp"].max()
        processing_time = end_time - start_time

        results.append({
            "norm_id": norm_id,
            "start_time": start_time,
            "end_time": end_time,
            "processing_time": processing_time,
            "num_frames": len(group)
        })

    results_df = pd.DataFrame(results)
    output_file = csv_file.replace(".csv", "_processing_times.csv")
    results_df.to_csv(output_file, index=False)
    print(f"✅ Processing times saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, help="Input CSV file")
    args = parser.parse_args()

    calculate_processing_times(args.file)
