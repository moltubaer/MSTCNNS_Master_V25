import os
import pandas as pd

# Re-define paths after code state reset
input_dir = "./csv"
output_dir = "./parsed_csv"
os.makedirs(output_dir, exist_ok=True)

# List all CSV files in the input directory
csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

# Process each CSV file
for file_name in csv_files:
    file_path = os.path.join(input_dir, file_name)
    df = pd.read_csv(file_path)

    # Ensure required columns exist
    if {'timestamp', 'direction', 'ran_ue_ngap_id'}.issubset(df.columns):
        results = []

        # Group by ran_ue_ngap_id
        grouped = df.groupby('ran_ue_ngap_id')

        for ue_id, group in grouped:
            if len(group) == 2:
                send_entry = group[group['direction'] == 'send']
                recv_entry = group[group['direction'] == 'recv']
                if not send_entry.empty and not recv_entry.empty:
                    delta = float(recv_entry['timestamp'].values[0]) - float(send_entry['timestamp'].values[0])
                    results.append({'ran_ue_ngap_id': ue_id, 'delta_ms': delta * 1000})  # Convert to ms

        # Create a DataFrame with results and write to output
        output_df = pd.DataFrame(results)
        output_file_path = os.path.join(output_dir, file_name)
        output_df.to_csv(output_file_path, index=False)

# Show the generated output files
os.listdir(output_dir)
