import pandas as pd
import matplotlib.pyplot as plt
import os

# Load the CSV file
df = pd.read_csv("./sys_csv/summary_output.csv")  # Change path if needed

# Extract numeric values from input_file for x-axis
df['input_number'] = df['input_file'].str.extract(r'(\d+)').astype(int)

# Define output directory
output_dir = "./plots/sys_mon"
os.makedirs(output_dir, exist_ok=True)

# CPU plot
plt.figure(figsize=(8, 5))
plt.plot(df['input_number'], df['avg_cpu_total'], marker='o', label='Avg CPU Total')
plt.plot(df['input_number'], df['max_cpu_total'], marker='o', label='Max CPU Total')
plt.xlabel('Number of UEs')
plt.ylabel('CPU Usage (%)')
plt.title('CPU Usage')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cpu_usage.png"))
plt.close()

# Memory Used (MB) plot
plt.figure(figsize=(8, 5))
plt.plot(df['input_number'], df['avg_mem_used_mb'], marker='o', label='Avg Mem Used (MB)')
plt.plot(df['input_number'], df['max_mem_used_mb'], marker='o', label='Max Mem Used (MB)')
plt.xlabel('Number of UEs')
plt.ylabel('Memory Used (MB)')
plt.title('Memory Usage')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "memory_usage_mb.png"))
plt.close()

# Memory Percent plot
plt.figure(figsize=(8, 5))
plt.plot(df['input_number'], df['avg_mem_percent'], marker='o', label='Avg Mem %')
plt.plot(df['input_number'], df['max_mem_percent'], marker='o', label='Max Mem %')
plt.xlabel('Number of UEs')
plt.ylabel('Memory Usage (%)')
plt.title('Memory Usage')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "memory_usage_percent.png"))
plt.close()

print(f"Plots saved to directory: {output_dir}")
