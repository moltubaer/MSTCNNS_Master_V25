import pandas as pd
import re
import argparse

def extract_numeric_id(identity):
    # Extract 10 last digits for UE identity
    match = re.search(r'(\d{10})$', identity)
    if match:
        return match.group(1)
    return identity

def calculate_processing_times(csv_file):
    df = pd.read_csv(csv_file)

    # Normalize to numeric identity
    df["norm_id"] = df["imsi"].apply(extract_numeric_id)

    results = []

    for norm_id in df["norm_id"].unique():
        # Find all rows where the decoded SUCI/IMSI contains the numeric ID
        pattern = re.compile(re.escape(norm_id))
        matches = df[df["imsi"].str.contains(pattern)]

        if matches.empty:
            print(f"⚠️ Warning: No matches found for {norm_id}")
            continue

        # Sort by timestamp to find first and last appearance
        sorted_matches = matches.sort_values(by="timestamp")

        first_row = sorted_matches.iloc[0]
        last_row = sorted_matches.iloc[-1]

        start_time = first_row["timestamp"]
        end_time = last_row["timestamp"]
        processing_time = end_time - start_time

        results.append({
            "norm_id": norm_id,
            "start_time": start_time,
            "end_time": end_time,
            "processing_time": processing_time,
            "first_frame": first_row["frame_number"],
            "last_frame": last_row["frame_number"],
            "num_frames": len(matches)
        })

    results_df = pd.DataFrame(results)
    output_file = csv_file.replace(".csv", "_processing_times.csv")

    # Use float precision without rounding off decimals
    results_df.to_csv(output_file, index=False, float_format='%.9f')
    print(f"✅ Processing times saved to {output_file}")

if __name__ == "__main__":
    path = "./csv/"
    input_file = "udm_ue_reg"

    calculate_processing_times(path + input_file + ".csv")
