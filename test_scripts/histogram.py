import numpy as np
import matplotlib.pyplot as plt

# --- parameters in seconds ---
mean_delay_s = 0.01        # 0.01 s  = 10 ms
sample_size  = 300

# --- generate samples (seconds) ---
rng = np.random.default_rng(seed=69)
inter_arrivals_s = rng.exponential(scale=mean_delay_s, size=sample_size)

# --- convert to milliseconds ---
inter_arrivals_ms = inter_arrivals_s * 1_000          # s → ms
mean_delay_ms     = mean_delay_s   * 1_000

# --- plot ---
plt.hist(inter_arrivals_ms, bins=20, density=True, alpha=0.7, color='blue')
plt.title(f"Exponential Distribution (mean = {mean_delay_ms:.1f} ms)")
plt.xlabel("Delay (ms)")
plt.ylabel("Density")
plt.grid(True)
plt.tight_layout()
plt.savefig("./histogram_ms.png")
plt.show()
