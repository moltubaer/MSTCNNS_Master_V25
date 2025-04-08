import numpy as np
import matplotlib.pyplot as plt

mean_delay = 0.001
sample_size = 300
inter_arrivals = np.random.exponential(scale=mean_delay, size=sample_size)

plt.hist(inter_arrivals, bins=20, density=True, alpha=0.7, color='blue')
plt.title(f"Exponential Distribution (mean = {mean_delay})")
plt.xlabel("Delay (seconds)")
plt.ylabel("Density")
plt.grid(True)
plt.show()
