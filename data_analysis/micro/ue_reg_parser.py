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

def process_csv_files(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    required_columns = {"timestamp", "direction"}

    for file_name in os.listdir(input_dir):
        if not file_name.endswith(".csv"):
            continue

        file_path = os.path.join(input_dir, file_name)
        df = pd.read_csv(file_path)

        # Skip files missing required columns
        if not required_columns.issubset(df.columns):
            print(f"Skipping {file_name} due to missing columns.")
            continue

        df["id"] = df.apply(extract_simple_numeric_id, axis=1)
        df = df.dropna(subset=["id", "timestamp", "direction"])

        results = []

        for id_val, group in df.groupby("id"):
            recv_entry = group[group["direction"] == "recv"].sort_values(by="timestamp").head(1)
            send_entry = group[group["direction"] == "send"].sort_values(by="timestamp").tail(1)

            if not recv_entry.empty and not send_entry.empty:
                delta = float(send_entry["timestamp"].values[0]) - float(recv_entry["timestamp"].values[0])
                results.append({
                    "id": int(id_val),
                    "recv_timestamp": recv_entry["timestamp"].values[0],
                    "send_timestamp": send_entry["timestamp"].values[0],
                    "delta_ms": delta * 1000  # full precision
                })

        # Write results
        output_df = pd.DataFrame(results)
        output_path = os.path.join(output_dir, file_name)
        output_df.to_csv(output_path, index=False)
        print(f"Processed: {file_name} → {output_path}")

# Example usage
if __name__ == "__main__":
    input_dir = "./csv"
    output_dir = "./parsed_csv"
    process_csv_files(input_dir, output_dir)
