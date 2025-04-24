import pandas as pd

df = pd.read_csv("/home/alexandermoltu/pcap_captures/04.24_14_09_system.csv")
avg_cpu = df["cpu_total"].mean()
max_cpu = df["cpu_total"].max()
avg_ram = df["mem_used_mb"].mean()
max_ram = df["mem_used_mb"].max()

print("Average CPU usage: ", round(avg_cpu, 2))
print("Max CPU usage: ", round(max_cpu, 2))
print("Average RAM (MB): ", round(avg_ram, 1))
print("Max RAM (MB): ", round(max_ram, 1))
