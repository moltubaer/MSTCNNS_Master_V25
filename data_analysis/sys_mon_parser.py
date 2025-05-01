import pandas as pd
import os

# Paths
input_folder = "./data/"
output_path = "./sys_csv/summary_output.csv"

# Ensure output directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Prepare list for summaries
summaries = []

# Iterate over all CSV files in the input directory
for file_name in os.listdir(input_folder):
    if file_name.endswith(".csv"):
        input_path = os.path.join(input_folder, file_name)
        try:
            df = pd.read_csv(input_path)

            summary = {
                "input_file": os.path.basename(file_name),
                "avg_cpu_total": round(df["cpu_total"].mean(), 2),
                "max_cpu_total": round(df["cpu_total"].max(), 2),
                "avg_mem_used_mb": round(df["mem_used_mb"].mean(), 2),
                "max_mem_used_mb": round(df["mem_used_mb"].max(), 2),
                "avg_mem_percent": round(df["mem_percent"].mean(), 2),
                "max_mem_percent": round(df["mem_percent"].max(), 2)
            }

            summaries.append(summary)
        except Exception as e:
            print(f"⚠️ Skipped {file_name}: {e}")

# Convert to DataFrame and save
summary_df = pd.DataFrame(summaries)
summary_df.to_csv(output_path, index=False)

print(f"✅ Summary saved to {output_path}")
