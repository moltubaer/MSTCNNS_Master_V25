import os
import pandas as pd

def extract_simple_numeric_id(row):
    """Extracts a simple numeric UE ID from ran_ue_ngap_id or IMSI/SUCI strings."""
    if pd.notna(row.get("id")):
        return int(str(row["id"]).strip())
    elif pd.notna(row.get("imsi")):
        digits = ''.join(filter(str.isdigit, str(row["imsi"])))
        if len(digits) >= 6:
            return int(digits[-6:])  # Use last 6 digits as ID
        elif digits:
            return int(digits)
    return None

def process_csv_file(input_file, output_file):
    df = pd.read_csv(input_file)

    if "timestamp" not in df.columns:
        print(f"Skipping {input_file} due to missing 'timestamp'.")
        return

    df["id"] = df.apply(extract_simple_numeric_id, axis=1)
    df = df.dropna(subset=["id", "timestamp"])

    results = []

    for id_val, group in df.groupby("id"):
        group_sorted = group.sort_values(by="timestamp")
        first = group_sorted["timestamp"].iloc[0]
        last = group_sorted["timestamp"].iloc[-1]
        delta = float(last) - float(first)
        results.append({
            "id": int(id_val),
            "first_timestamp": first,
            "last_timestamp": last,
            "delta_ms": delta * 1000  # milliseconds
        })

    output_df = pd.DataFrame(results)
    output_df = output_df[output_df["delta_ms"] != 0]  # Exclude zero-duration entries
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    output_df.to_csv(output_file, index=False)

    print(f"Processed: \t {os.path.basename(input_file)} → {os.path.basename(output_file)}")
    print(f"Entries: \t {len(output_df)}")
    print()

def process_csv_recursively(input_root, output_root):
    for root, _, files in os.walk(input_root):
        for file in files:
            if not file.endswith(".csv"):
                continue
            input_path = os.path.join(root, file)
            relative_path = os.path.relpath(input_path, input_root)
            output_path = os.path.join(output_root, relative_path)
            process_csv_file(input_path, output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Recursively parse UE reg/dereg CSVs and output processed results.")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing raw CSV files.")
    parser.add_argument("--output", "-o", required=True, help="Output directory to store processed CSVs.")
    args = parser.parse_args()

    process_csv_recursively(args.input, args.output)
